"""
scred/project.py

Uses REDCap interface and data types defined in other modules to create more complex
classes.
"""

from . import webapi
from . import dtypes
from .config import DEFAULT_SETTINGS, USER_CFG, RedcapConfig

# ---------------------------------------------------
# To construct requester based on class of `requester` arg in RedcapProject.
# All of this might belong in webapi.py though...

def _requester_from_config(cfg):
    return webapi.RedcapRequester(cfg)

def _requester_from_token(token):
    if len(token) != 32:
        raise ValueError(f"REDCap tokens should be 32 characters long. Got {len(token)}")
    cfg = DEFAULT_SETTINGS
    cfg.update({"token": token})
    return webapi.RedcapRequester(RedcapConfig(cfg))

def _requester_reflexive(requester):
    # If already given a requester, just bounce back
    return requester

def _requester_from_default():
    # Fall back to contents of `scred/config.json`
    return webapi.RedcapRequester(USER_CFG)

def _get_requester_dispatcher():
    # Avoids polluting global namespace
    return {
        RedcapConfig: _requester_from_config,
        str: _requester_from_token,
        webapi.RedcapRequester: _requester_reflexive,
    }

def _create_requester(construct_arg):
    # Called when init'ing RedcapProject to make arg type flexible
    if not construct_arg:
        return _requester_from_default()
    argclass = construct_arg.__class__
    dispatcher = _get_requester_dispatcher()
    try:
        constructor = dispatcher[argclass]
    except KeyError:
        raise TypeError(
            "Project must be built from token (str), config, or None, not",
            f"{construct_arg}"
        ) 
    return constructor(construct_arg)

# ---------------------------------------------------
   
class RedcapProject:
    def __init__(self, requester = None, *args, **kwargs):
        self.requester = _create_requester(requester)

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
        return self.requester.post(payload_kwargs)
    
    def post(self, **kwargs):
        return self.requester.post(**kwargs)


