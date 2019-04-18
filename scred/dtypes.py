"""
dtypes.py

Defines classes whose instances represent various REDCap responses.
"""

import re
from typing import Collection

import pandas as pd

# ---------------------------------------------------

# TODO: Make this configurable, not everyone uses our ID scheme
# Maybe set it somewhere in config so it can be overwritten for
# a project? Default to None, and only check if not None?
ID_TEMPLATE = re.compile(r"[A-Z]{3}[1-9][0-9]{7}")
# Could also make ID_TEMPLATE a class-level property of Record


class Record(pd.DataFrame):
    """
    Represents a single observation in a REDCap project.
    """
    def __init__(self, id_key: str, data: dict = dict()):
        """
        REDCap API will present a list of dicts; each dict is one record. We create a
        record from a response dict and can handle bulk pulls with loops/RecordSet.
        """
        print("Creating a record instance...")
        self._id = data[id_key]
        super().__init__(data)
    
    @property
    def id(self):
        return self._id
    
    @id.setter
    def id(self, value):
        # Confirm the subject ID at least looks real
        if not ID_TEMPLATE.match(value):
            raise ValueError(f"Invalid ID: {value}")
        self._id = value


class RecordSet(pd.DataFrame):
    def __init__(self, records: Collection[Record]):
        """
        Use the record IDs to build an Index.
        """
        # will this work if r.index is also multi?
        # look into .from_frame()
        idx = pd.MultiIndex([ (r.id, r.index) for r in records ])
        # Make data a property..?
        self._data = pd.DataFrame(index=idx)


class DataDictionary(pd.DataFrame):
    """ 
    Represents a REDCap Metadata/Data Dictionary object for a given project.
    At least to start, we are only creating these from JSON data returned by API.
    So we work from a list of dicts.

    Columns: actual_name_in_returned_json
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
    def __init__(self, rawdata):
        # Use JSON data to create DataFrame
        super().__init__(rawdata)
    
    def add_response(self, field, response):
        """
        field can be a single field (str) or container of several (set, list, etc).
        response is a map.
        """
        # Put new responses into right format
        notdone = ""
        for code, label in response.items():
            notdone += f"{code}, {label} | "
            # Remember that we only need first | if options already exist
        # If only one field given, put it into a list
        if isinstance(field, str):
            field = [field]
        for somefield in field:
            choices = self.loc[ self['field_name']==field, 'select_choices_or_calculations' ]
            # TODO: Finish implementing
            # add new choices here


class DataAccessGroup:
    pass
