"""
dtypes.py

Defines classes whose instances represent various REDCap responses.
"""

import re
import warnings
from typing import Collection

import pandas as pd

from . import backfillna

# ---------------------------------------------------

# TODO: Make this configurable, not everyone uses our ID scheme
# Maybe set it somewhere in config so it can be overwritten for
# a project? Default to None, and only check if not None?


class Record(pd.DataFrame):
    """
    Represents a single observation in a REDCap project.
    """
    NACODE = -555 # "Not applicable" (branching logic not satisfied)
    BADCODE = -444 # "Bad data" (unexplained blank field)
    ID_TEMPLATE = re.compile(r"[A-Z]{3}[1-9][0-9]{7}") # ID must match this
    def __init__(self, id_key: str, data: dict = dict()):
        """
        REDCap API will present a list of dicts; each dict is one record. We create a
        record from a response dict and can handle bulk pulls with loops/RecordSet.
        """
        idx = pd.Index(data.keys(), name="field_name")
        responses = pd.Series(
            index=idx,
            data=list(data.values()),
            name="response",
        )
        super().__init__(index=idx, data=responses)
        self._id = data[id_key]
        self._nafilled = False # "Not Applicable"
        self._bdfilled = False # "Bad Data (possible RA error)"
    
    @property
    def id(self):
        return self._id
    
    @id.setter
    def id(self, value):
        # Confirm the subject ID at least looks real
        if not Record.ID_TEMPLATE.match(value):
            raise ValueError(f"Invalid ID format: {value}")
        self._id = value

    def require_column(self, col, default_value = ""):
        # Could make this a decorator
        if col not in self.columns.array:
            self[col] = default_value


    def add_branching_logic(self, datadict):
        self.require_column("branching_logic")
        if datadict.blogic_fmt == "redcap":
            datadict.make_logic_pythonic()
        for varname in self.index:
            # TODO: Switch to using exportFieldNames to avoid ____ from negatives.
            # OK for current uses but potentially problematic.
            base_field = varname
            if "___" in varname:
                base_field = varname.split("___")[0]
            try:
                base_logic = datadict.loc[base_field, "branching_logic"]
                self.loc[varname, "branching_logic"] = base_logic
            # Overflow variables like `{instrument}_complete`
            except KeyError:
                warnings.warn(f"Cannot find {varname} in record and/or datadict")
                self.loc[varname, "branching_logic"] = ""


    def _fill_na_values(self, datadict):
        """
        Using a pythonic `branching_logic` column, fill in Non-Applicable REDCap values. 
        That is, if branching logic is NOT satisfied, we expect the field to be blank and 
        assign the "valid missing: N/A" code.
        """
        if self._nafilled is True:
            return
        if "branching_logic" not in self.columns.array:
            raise AttributeError("No branching_logic column exists")
        parser = backfillna.Parser(self)
        parser.parse_all_logic()
        namask = (parser.data["response"]=="") & (parser.data["LOGIC_MET"]==False)
        parser.data.loc[namask, "response"] = Record.NACODE
        # Transfer filled responses to this object and set attribute
        self.loc[:, "response"] = parser.data.loc[:, "response"]
        self._nafilled = True
    

    def _fill_bad_data(self):
        """
        Once N/A values are filled in, anything remaining is missing due to RA error or
        something else problematic enough to flag.
        """
        if self._nafilled is False:
            raise AttributeError("Cannot fill missing values until NA values are filled")
        self.loc[ self["response"]=="", "response" ] = Record.BADCODE
        self._bdfilled = True


    def fill_missing(self, datadict):
        """
        Composite method to handle all logic conversion and backfilling.
        """
        self.add_branching_logic(datadict)
        self._fill_na_values(datadict)
        self._fill_bad_data()
        self["response_uncoerced"] = self["response"] # preserve text
        self["response"] = pd.to_numeric(self["response"], errors="coerce")


class RecordSet(pd.DataFrame):
    def __init__(self, records: Collection[Record]):
        """
        Use the record IDs to build an Index.
        """
        # will this work if r.index is also multi?
        # look into .from_frame()
        idx = pd.MultiIndex([ (r.id, r.index) for r in records ])
        # Make data a property..?
        self._data = pd.DataFrame(data=records, index=idx)

# ===================================================

class DataDictionary(pd.DataFrame):
    """ 
    Represents a REDCap Metadata/Data Dictionary object for a given project.
    At least to start, we are only creating these from JSON data returned by API.
    So we work from a list of dicts.

    <Column Label: actual_name_in_returned_json>
        Variable / Field Name: field_name
        Form Name: form_name
        Section Header: section_header
        Field Type: field_type
        Field Label: field_label
        Choices, Calculations, OR Slider Labels: select_choices_or_calculations
        Field Note: field_note
        Text Validation Type OR Show Slider Number: text_validation_type_or_show_slider_number
        Text Validation Min: text_validation_min
        Text Validation Max: text_validation_max
        Identifier?: identifier
        Branching Logic (Show field only if...): branching_logic
        Required Field?: required_field
        Custom Alignment: custom_alignment
        Question Number (surveys only): question_number
        Matrix Group Name: matrix_group_name
        Matrix Ranking?: matrix_ranking
        Field Annotation: field_annotation
    """
    def __init__(self, data, blogic_fmt="redcap"):
        # Use JSON data to create DataFrame, but store API response
        idx = pd.Index(
            [ d["field_name"] for d in data ],
            name="field_name",
        )
        super().__init__(data, index=idx)
        self.raw_response = data
        self._blogic_fmt = blogic_fmt
    
    # ---------------------------------------------------
    # Properties, static methods, "private" functions
    @property
    def blogic_fmt(self):
        # Branching logic format
        return self._blogic_fmt

    @blogic_fmt.setter
    def blogic_fmt(self, value: str):
        valid = ["python", "redcap"]
        if value not in valid:
            raise ValueError(f"{value} is not available. Choose from {valid}")
        self._blogic_fmt = value

    @staticmethod
    def _convert_logic_syntax(metadata_row):
        """
        Handles all non-checkbox fields' logic conversions.
        """
        bouncebacks = [None, ""]
        blogic = metadata_row["branching_logic"]
        if blogic not in bouncebacks:
            clean = blogic.replace("[", "").replace("]", "")
            clean = clean.replace("=", "==") # next lines fix >== and <==
            clean = clean.replace(">==", ">=") # TODO: use Will's masking trick
            clean = clean.replace("<==", "<=")
            clean = clean.replace("'", "")
            return clean
        return ""

    @staticmethod
    def _convert_checkbox_export(cbseries):
        """
        Checkbox forms are exported differently in logic than in data; fix by substitution. 
            DO change: 'nonpsych_meds_cat(999) == 1' becomes 'nonpsych_meds_cat___999 == 1'.
            DON'T change: '(nonpsych_meds == 1 or nonpsych_meds == -777)' stays as-is.
        """
        if not isinstance(cbseries, pd.Series):
            raise TypeError(f"Requires series, not {cbseries.__class__}")
        return cbseries.replace(
            to_replace=r"(?P<varprefix>\w+)\(-?(?P<numcode>\d+)\)", 
            value=r"\g<varprefix>___\g<numcode>",  
            regex=True,
        )

    # ---------------------------------------------------
    # Core functionality
    def make_logic_pythonic(self):
        """
        Convert REDCap's logic syntax to be evaluable by Python.
        TODO: Not good! Use exportFieldNames or whatever and do it differently.
        """
        if self.blogic_fmt == "python":
            return
        fieldlogic = dict()
        # Converts all fields that are not checkbox exports
        for adict in self.raw_response:
            logic = self._convert_logic_syntax(adict)
            varname = adict['field_name']
            fieldlogic[varname] = logic
        # Make that into a series, pass to checkbox converter, overwrite
        all_but_checkboxes = pd.Series(fieldlogic)
        self["branching_logic"] = self._convert_checkbox_export(all_but_checkboxes)
        self.blogic_fmt = "python"

# ===================================================

class DataAccessGroup:
    pass



    
