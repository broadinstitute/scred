"""
scred/project.py

Uses REDCap interface and data types defined in other modules to create more complex
classes. Can't go in `dtypes` module because it relies on the `webapi` module, which
lives "above" `dtypes` in the hierarchy.
"""

from . import webapi
from . import dtypes

# ---------------------------------------------------
   
class RedcapProject:
    """
    Main class for top-level interaction. Requires a token and url to create requester.
    """
    def __init__(self, url, token, metadata = None, requester_kwargs = None):
        if requester_kwargs is None:
            requester_kwargs = dict()
        self.requester = webapi.RedcapRequester(
            token=token,
            url=url,
            **requester_kwargs,
        )
        self._metadata = None

    @property
    def metadata(self):
        """
        Property that holds the metadata (Data Dictionary) for this project instance.
        """
        if self._metadata is None:
            self._metadata = dtypes.DataDictionary(self.post(content="metadata"))
        return self._metadata
    
    @metadata.setter
    def metadata(self, value):
        if not isinstance(value, (dtypes.DataDictionary, None)):
            raise TypeError("metadata must be None or DataDictionary")
        self._metadata = value

    @property
    def url(self):
        return self.requester.url

    def post(self, **kwargs):
        return self.requester.post(**kwargs)

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
            payload_kwargs.update(field=",".join(fields))
        return self.post(payload_kwargs)
    
    def get_records(self, records = None, fields = None, **kwargs):
        """
        Export a set of records from the given project. Optional arguments also include:
            -forms (replace spaces with _)
            -dateRangeBegin
            -dateRangeEnd
        For dateRange options, format as YYYY-MM-DD HH:MM:SS. Records retrieved are created
        OR modified within that range, and time boundaries are exclusive.
        """
        payload = {"content": "record"}
        if records:
            payload.update(records=",".join(records))
        if fields:
            payload.update(fields=",".join(fields))
        return self.post(**payload, **kwargs).json()

