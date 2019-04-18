"""
scred/project.py

Uses REDCap API and data types defined in other modules to create more complex
classes.
"""

from . import webapi
from . import dtypes
"""
https://docs.python.org/3/reference/import.html
5.7 (5.7.1): Helps explain the need for `from . import _`:

Depending on how __main__ is initialized, __main__.__spec__ gets set appropriately or to None.

When Python is started with the -m option, __spec__ is set to the module spec of the corresponding module
or package. __spec__ is also populated when the __main__ module is loaded as part of executing a directory,
zipfile or other sys.path entry.

Note that __main__.__spec__ is always None in the last case, even if the file could technically be imported
directly as a module instead. Use the -m switch if valid module metadata is desired in __main__.
"""

class RedcapProject:
    def __init__(self, requester_or_config = None, *args, **kwargs):
        print("Creating instance of RedcapProject...")
        if requester_or_config is None:
            config.load_config_from_file_if_valid()
        self._post_request = "placeholder"
        # Obviously this is placeholder but you get the point
    
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
