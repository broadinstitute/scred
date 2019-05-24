"""
dtypes.py

Defines classes to represent various REDCap objects.
"""

import re
import warnings
from typing import Collection

import pandas as pd

from . import backfillna

# ---------------------------------------------------

class Record(pd.DataFrame):
    """
    Represents a single observation in a REDCap project. Raw data will be blank whether 
    the question was skipped or not, so we fill in the Not Applicable (N/A) and True Missing 
    (RA error, other issue) data separately. The process by which skipped fields are filled, 
    then missing fields are filled afterwards, is tracked by properties .nafilled and .bdfilled
    """
    NACODE = -555 # "Not applicable" (branching logic not satisfied)
    BADCODE = -444 # "Bad data" (unexplained blank field)
    # ID_TEMPLATE = re.compile(r"[A-Z]{3}[1-9][0-9]{7}") # ID must match this
    ID_TEMPLATE = re.compile(r".*") # default: Everything is permitted
    # TODO: Make template configurable, not everyone uses our ID scheme.
    # Have a classmethod to call before initing? Then user can pass an RE if they want.
    # Record.set_template(r"some_regex"); participant = Record(my_data)
    def __init__(self, id_key: str, data: dict = dict()):
        """
        REDCap API will present a list of dicts; each dict is one record. We create a
        record from a response dict and can handle bulk pulls with loops/RecordSet.
        """
        redcap_fields, responses = data.keys(), data.values()
        idx = pd.Index(redcap_fields, name="field_name")
        response_series = pd.Series(
            index=idx,
            data=list(responses),
            name="response",
        )
        super().__init__(index=idx, data=response_series)
        self._id = data[id_key]
        self.nafilled = False # "Not Applicable" filled in
        self.bdfilled = False # "Bad Data (possible RA error)" filled in
    
    @property
    def id(self):
        return self._id
    
    @id.setter
    def id(self, value):
        # Confirm the subject ID matches ID template
        if not Record.ID_TEMPLATE.match(value):
            raise ValueError(f"Invalid ID format: {value}")
        self._id = value

    def __str__(self):
        return f"{self.__class__.__name__}: {self.id}"

    def require_column(self, col, default_value = "", flexible = True):
        # TODO? Could make this a decorator. If I do, think I can put name of calling func in error
        if col in self.columns.array:
            return
        if not flexible:
            raise AttributeError(f"Cannot run <this function> without column {col}")
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
            # Keep blank for overflow variables like `{instrument}_complete`
            except KeyError:
                warnings.warn(f"Cannot find {varname} in record and/or datadict")
                self.loc[varname, "branching_logic"] = ""


    def _fill_na_values(self, datadict):
        """
        Using a pythonic `branching_logic` column, fill in Non-Applicable REDCap values. 
        That is, if branching logic is NOT satisfied, we expect the field to be blank and 
        assign the "valid missing: N/A" code.
        """
        if self.nafilled is True:
            return
        self.require_column("branching_logic", flexible=False)
        parser = backfillna.Parser(self)
        parser.parse_all_logic()
        namask = (parser.data["response"]=="") & (parser.data["LOGIC_MET"]==False)
        parser.data.loc[namask, "response"] = Record.NACODE
        # Transfer filled responses to this object and set tracking attribute
        self.loc[:, "response"] = parser.data.loc[:, "response"]
        self.nafilled = True


    def _fill_bad_data(self):
        """
        Once N/A values are filled in, anything remaining is missing due to RA error or
        something else problematic enough to flag.
        """
        if self.nafilled is False:
            raise AttributeError("Cannot fill missing values until NA values are filled")
        self.loc[ self["response"]=="", "response" ] = Record.BADCODE
        self.bdfilled = True


    def to_numeric(self):
        """
        Cast all elements of the 'response' column to numeric. If there is no valid
        conversion, the field will become `np.nan`. A copy of the original response 
        is kept in 'response_uncoerced' to preserve text.
        """
        self["response_uncoerced"] = self["response"]
        self["response"] = pd.to_numeric(self["response"], errors="coerce")


    def fill_missing(self, datadict):
        """
        Composite method to handle all logic conversion and backfilling. Convenience
        feature for users; recommended you use this when implementing.
        """
        self.add_branching_logic(datadict)
        self._fill_na_values(datadict)
        self._fill_bad_data()
        self.to_numeric()


class RecordSet(dict):
    """
    Maps a record's ID to its object to simplify lookups. Provides a convenient interface
    for operating on multiple records together.
    """
    # ID_TEMPLATE = re.compile(r"[A-Z]{3}[1-9][0-9]{7}") # Where should this live?
    ID_TEMPLATE = re.compile(r".*") # default: Everything is permitted
    # ID_TEMPLATE should probably be in Record. RecordSet should get a method to change
    # Record's class property, maybe...? Not sure how to handle this yet.
    def __init__(self, records: Collection[Record], id_key: str):
        """
        Take a bulk record data response from the REDCap API and, for each record,
        instantiate a Record. Use the `id_key` provided to the RecordSet and pass it 
        to the Record constructor. If the given records are already processed, skip that 
        step and include them directly.
        """
        for record in iter(records):
            instance = record
            if not isinstance(record, Record):
                instance = Record(id_key=id_key, data=record)
            self[instance.id] = instance

    def __setitem__(self, key, value):
        if not Record.ID_TEMPLATE.match(key):
            raise ValueError(f"ID did not match template: {key}")
        super().__setitem__(key, value)


    def fill_missing(self, datadict: "DataDictionary"):
        """
        Iterate over records contained in this set. Call fill_missing method on
        each individual record; these are instances of scred.dtypes.Record, so we
        know that method exists and expect it to function in isolation. The given
        data dictionary, `datadict`, is used to look up branching logic.
        """
        for record in iter(self.values()):
            record.fill_missing(datadict)
            

    def as_dataframe(self):
        df = pd.DataFrame()
        # TODO: Implement! Look into .from_frame()
        # idx = pd.MultiIndex([ (r.id, r.index) for r in self.values() ])
        # df = pd.DataFrame(data=self, index=idx)
        return df

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
        """
        Index on field names with other metadata as columns. .blogic_fmt represents
        the current branching logic format. When working from API response, this is
        always going to start off as REDCap-formatted.
        """
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
    # TODO: Implement
    pass


