"""
scred/project.py

Uses REDCap API and data types defined in other modules to create more complex
classes.
"""

from . import webapi
from . import dtypes

# ---------------------------------------------------

class RedcapProject:
    def __init__(self, requester_or_config_or_token = None, *args, **kwargs):
        print("Creating instance of RedcapProject...")
        if requester_or_config is None: # default to config stored in project
            config.load_config_from_file(config.USER_CFG)
        self._post_request = "placeholder"
        # Obviously this is placeholder but you get the point

    @classmethod
    def _init_from_token(cls, token):
        self._token = token
        self._url = DEFAULT_URL
    
    # Liking the "top line of docstring for source" thing
    def get_export_fieldnames(self, fields = None):
        """ (From REDCap documentation)
        This method returns a list of the export/import-specific version of field names for all fields
        (or for one field, if desired) in a project. This is mostly used for checkbox fields because
        during data exports and data imports, checkbox fields have a different variable name used than
        the exact one defined for them in the Online Designer and Data Dictionary, in which *each checkbox
        option* gets represented as its own export field name in the following format: field_name +
        triple underscore + converted coded value for the choice. For non-checkbox fields, the export
        field name will be exactly the same as the original field name. Note: The following field types
        will be automatically removed from the list returned by this method since they cannot be utilized
        during the data import process: 'calc', 'file', and 'descriptive'.

        The list that is returned will contain the three following attributes for each field/choice:
        'original_field_name', 'choice_value', and 'export_field_name'. The choice_value attribute
        represents the raw coded value for a checkbox choice. For non-checkbox fields, the choice_value
        attribute will always be blank/empty. The export_field_name attribute represents the export/import-
        specific version of that field name.
        """
        payload_kwargs = {"content": "exportFieldNames"}
        if fields:
            payload_kwargs.update(field=fields)
        return self._post_request(payload_kwargs)


# Want this available as top-level, but would be nice to bind a reduced
# version to the Project itself.
def add_branching_logic(record_set, data_dict):
    """
    each record has the same fields.
    those fields are the records' indexes.
    a RecordSet can hold a "fields_in_records" property.
    the DataDictionary has columns for field name and branching logic.
    pull fields_in_records and merge with DataDict.logic to get df of
        field_name, logic_statement.
    for each record, call that branching logic on the record's data.
    the altered records are used to fill in a new RecordSet, which we return.
    """
    """
    ~~PSEUDO~~
    recset = RecordSet()
    dd = DataDictionary()
    rfields = recset.fields
    blogic = dd.blogic
    for record in recset:
        altered = backfillna(record.data, blogic)
        recset[record] = altered
    return recset
    """

