# webapi.py

# Creates the request-sending class used to interact with a REDCap instance.

# External dependencies
import requests
# Internal dependencies
import config
import dtypes

user_cfg = config.USER_CFG

# ---------------------------------------------------

class RedcapRequester:
    def __init__(self, config.RedcapConfig: cfg = user_cfg):
        self._config = cfg
        self._payloader = __class__._build_payloader(cfg)


    @staticmethod
    def _build_payloader(cfg):
        def payloader(**kwargs):
            '''Constructs the payload for a request.'''
            payload = {
                'token': cfg['token'],
                'url': cfg['url'],
                'default_format': cfg['default_format'],
            }
            payload.update(kwargs)
            return payload
        return payloader


    def send_post_request(self, **kwargs):
        payload = self._payloader(**kwargs)
        response = requests.post(self._config['url'], payload)
        if not response.ok:
            msg = (
                "Couldn't complete request. Code "
                f"{response.status_code}: {response.reason}."
            )
            raise requests.HTTPError(msg)
        else:
            return response.json()


    # should this be a property called `version`?
    def get_redcap_version(self):
        return self.send_post_request(content="version")


    # NOTE: Return the JSON data, not the instance of DataDictionary
    def get_data_dictionary(self):
        pass
        # TODO: Implement
        # return dtypes.DataDictionary(response_data)

    
    def get_export_fieldnames(self, fields=None):
        '''
        (From REDCap documentation)
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
        '''
        payload_kwargs = {"content": "exportFieldNames"}
        if fields:
            payload_kwargs.update(field=fields)
        return self.send_post_request(payload_kwargs)
