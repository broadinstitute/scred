"""
dtypes.py

Defines classes to represent various REDCap objects.
"""

import re
import json
import warnings
from typing import Collection, Optional, Dict

import pandas as pd

from . import backfillna

# ---------------------------------------------------


class Record(pd.DataFrame):
    """
    Represents a single observation in a REDCap project. Raw data will
    be blank whether the question was skipped or not, so we fill in the
    Not Applicable (N/A) and True Missing (RA error, other issue) data
    separately. The process by which skipped fields are filled, then
    missing fields are filled afterwards, is tracked by properties
    `.nafilled and .bdfilled`
    """

    NACODE = -555  # "Not applicable" (branching logic not satisfied)
    BADCODE = -444  # "Bad data" (unexplained blank field)
    ID_TEMPLATE = re.compile(r".*")  # default: Everything is permitted
    # TODO: Make template configurable, not everyone uses our ID scheme.
    # Call a classmethod before init? User can pass RE if they want.
    # Record.set_template(r"some_regex"); participant = Record(my_data)

    def __init__(self, primary_key: str, data: Optional[Dict] = None):
        """
        REDCap API will return a list of dicts; each dict is one record.
        We create a record from a response dict and can handle bulk
        pulls with loops/RecordSet.
        """
        if data is None:
            data = dict()
        redcap_fields, responses = data.keys(), data.values()
        idx = pd.Index(redcap_fields, name="field_name")
        response_series = pd.Series(
            index=idx, data=list(responses), name="response"
        )
        super().__init__(index=idx, data=response_series)
        self._id = data[primary_key]
        self.nafilled = False  # "Not Applicable" filled in
        self.bdfilled = False  # "Bad Data (possible RA error)" filled in

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        # Confirm the subject ID matches ID template
        if not Record.ID_TEMPLATE.match(value):
            raise ValueError(f"Invalid ID format: {value}")
        self._id = value

    def require_column(self, col, default_value="", flexible=True):
        # TODO? Could make this a decorator. If I do,
        # think I can put name of calling func in error
        if col in self.columns.array:
            return
        if not flexible:
            raise AttributeError(
                f"Cannot run <this function> without column {col}"
            )
        self[col] = default_value

    def add_branching_logic(self, datadict):
        """
        Draws from metadata object to add branching logic to record.
        Do I want a new class called LogicFiller that operates on
        records? Seems like half of this class is just logic-filling.
        Maybe mixin with Parser? Or LogicFiller has/makes a Parser?
        """
        self.require_column("branching_logic")
        if datadict.blogic_fmt == "redcap":
            datadict = datadict.copy()
            datadict.make_logic_pythonic()
        for varname in self.index:
            base_field = varname
            if "___" in varname:
                base_field = varname.split("___")[0]
                assert datadict.loc[base_field, "field_type"] == "checkbox"
            try:
                base_logic = datadict.loc[base_field, "branching_logic"]
                self.loc[varname, "branching_logic"] = base_logic
            # Keep blank for overflow variables
            # like `{instrument}_complete`
            except KeyError:
                self.loc[varname, "branching_logic"] = ""
                if not varname.endswith("_complete"):
                    # "_complete" fields not expected in datadict
                    warnings.warn(
                        f"Cannot find {varname} in record and/or datadict"
                    )

    def _fill_na_values(self, metadata):
        """
        Using a pythonic `branching_logic` column, fill in Non-
        Applicable REDCap values. That is, if branching logic is NOT
        satisfied, we expect the field to be blank and assign the "valid
        missing: N/A" code.
        """
        if self.nafilled is True:
            return
        self.require_column("branching_logic", flexible=False)
        # checkboxes = metadata.checkboxes
        parser = backfillna.Parser(self)
        parser.parse_all_logic()
        namask = (
            (parser.data["response"] == "")
            # bitmask means we need ==, not 'is'
            & (parser.data["LOGIC_MET"] == False)
        )
        cbna = (
            (parser.data["response"].isin([0, "0"]))
            # bitmask means we need ==, not 'is'
            & (parser.data["LOGIC_MET"] == False)
            & (parser.data.index.str.contains("___"))
        )
        parser.data.loc[namask, "response"] = Record.NACODE
        parser.data.loc[cbna, "response"] = Record.NACODE
        # Transfer filled responses to object and set tracking attribute
        self.loc[:, "response"] = parser.data.loc[:, "response"]
        self.nafilled = True

    def _fill_bad_data(self):
        """
        Once N/A values are filled in, anything remaining is missing
        due to RA error or something else problematic enough to flag.
        """
        if self.nafilled is False:
            raise AttributeError(
                "Cannot fill missing values until NA values are filled"
            )
        self.loc[self["response"] == "", "response"] = Record.BADCODE
        self.bdfilled = True

    def fill_missing(self, metadata):
        """
        Composite method to handle all logic conversion and backfilling.
        Convenience feature for users; recommended you use this when
        implementing a pipeline.
        """
        self.add_branching_logic(metadata)
        self._fill_na_values(metadata)
        self._fill_bad_data()

    def rcvalue(self, field):
        """
        Used to more easily access numeric data in the `response`
        column. Only needs a field name; automatically gets response
        and attempts to make it numeric.
        """
        try:
            value = self.loc[field, "response"]
        except KeyError as ex:
            raise ValueError(f"Invalid field: {ex}")
        converter = int
        if isinstance(value, str) and "." in value:
            converter = float
        try:
            return converter(value)
        except (ValueError, TypeError):
            return value

    def alter_value(self, field, new_value):
        """
        Used to change a stored value using underlying DataFrame's
        `.loc` method. Abstracts away column names.
        """
        try:
            self.loc[field, "response"]
        except KeyError:
            warnings.warn(f"{field} was not an existing key; creating new row")
        self.loc[field, "response"] = new_value


class RecordSet(dict):
    """
    Maps a record's ID to its object to simplify lookups. Provides a
    convenient interface for operating on multiple records as a unit.
    """

    ID_TEMPLATE = re.compile(r".*")  # default: Everything is permitted
    # ID_TEMPLATE should probably be in Record. RecordSet should get a
    # method to change Record's class property, maybe...? Not sure yet.

    def __init__(self, records: Collection[Record], primary_key: str):
        """
        Take a bulk record data response from the REDCap API and, for
        each record, instantiate a Record. Use the `primary_key`
        provided to the RecordSet and pass it to the Record constructor.
        If the given records are already processed, skip that step and
        include them directly.
        """
        for record in records:
            instance = record
            if not isinstance(record, Record):
                instance = Record(primary_key=primary_key, data=record)
            self[instance.id] = instance

    def __setitem__(self, key, value):
        if not Record.ID_TEMPLATE.match(key):
            raise ValueError(f"ID did not match template: {key}")
        super().__setitem__(key, value)

    def fill_missing(self, metadata: "DataDictionary"):
        """
        Iterate over records contained in this set. Call fill_missing
        method on each individual record; these are instances of
        scred.dtypes.Record, so we know that method exists and expect
        it to function in isolation. The given data dictionary,
        `metadata`, is used to look up branching logic.
        """
        for record in self.values():  # TODO: Add tests
            if not (record.bdfilled and record.nafilled):
                record.fill_missing(metadata)

    def as_dataframe(self):
        df = pd.DataFrame()
        # TODO: Implement! Look into .from_frame()
        # idx = pd.MultiIndex([(r.id, r.index) for r in self.values()])
        # df = pd.DataFrame(data=self, index=idx)
        return df


# ===================================================


class DataDictionary(pd.DataFrame):
    """
    Represents REDCap Metadata/Data Dictionary object for given project.
    To start, only creating these from JSON data returned by API.
    That is, we work from a list of dicts.

    <Column Label: actual_name_in_returned_json>
        Variable / Field Name: field_name
        Form Name: form_name
        Section Header: section_header
        Field Type: field_type
        Field Label: field_label
        Choices, Calculations, OR Slider Labels:
            select_choices_or_calculations
        Field Note: field_note
        Text Validation Type OR Show Slider Number:
            text_validation_type_or_show_slider_number
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
        Index on field names with other metadata as columns.
        .blogic_fmt represents the current branching logic format.
        When working from API response, this is always going to start
        off as REDCap-formatted.
        """
        if isinstance(data, pd.DataFrame):
            super().__init__(data)
        else:
            idx = pd.Index([d["field_name"] for d in data], name="field_name")
            super().__init__(data, index=idx)
        self._blogic_fmt = blogic_fmt

    @property
    def blogic_fmt(self):
        """
        Branching logic format.
        """
        return self._blogic_fmt

    @property
    def checkboxes(self):
        mask = self["field_type"] == "checkbox"
        return self.loc[mask, "field_name"].tolist()

    @blogic_fmt.setter
    def blogic_fmt(self, value: str):
        valid = ["python", "redcap"]
        if value not in valid:
            raise ValueError(f"{value} is not available. Choose from {valid}")
        self._blogic_fmt = value

    @staticmethod
    def _logic_statement_to_python(blogic):
        """
        Handles all REDCap fields' logic conversions, going from REDCap
        syntax to python-interpretable code.
        """
        bouncebacks = [None, ""]
        if blogic in bouncebacks:
            return ""
        clean = re.sub(r"[\[\]']", "", blogic)
        clean = re.sub(r"([^<>])(=)", r"\g<1>==", clean)
        clean = DataDictionary.convert_checkbox_names(clean)
        return clean

    @staticmethod
    def convert_checkbox_names(blogic):
        """
        Checkbox forms are exported differently in logic than in data;
        fix by substitution.
            DO change:
                'nonpsych_meds_cat(999) == 1' becomes
                'nonpsych_meds_cat___999 == 1'.
            DON'T change:
                '(nonpsych_meds == 1 or nonpsych_meds == -777)'
                stays as-is.
        """
        pattern = re.compile(
            r"(?P<field>\w+)\(" r"(?P<neg>-?)" r"(?P<choice>\d+)\)"
        )
        return re.sub(
            pattern,
            lambda m: f"{m['field']}___{'_' if m['neg'] else ''}{m['choice']}",
            blogic,
        )

    def make_logic_pythonic(self):
        """
        Convert REDCap's logic syntax to be evaluable by Python.
        """
        if self.blogic_fmt == "python":
            return
        fieldslogic = dict()
        # TODO: Is it faster to just use .loc instead of JSONifying?
        # Profile.
        for fdict in json.loads(self.to_json(orient="records")):
            rclogic = fdict["branching_logic"]
            pylogic = self._logic_statement_to_python(rclogic)
            varname = fdict["field_name"]
            fieldslogic[varname] = pylogic
        self["branching_logic"] = pd.Series(fieldslogic)
        self.blogic_fmt = "python"

    def copy(self):
        df_copy = super().copy()
        return self.__class__(df_copy, blogic_fmt=self.blogic_fmt)


# ===================================================


class DataAccessGroup:
    # TODO: Implement
    pass
