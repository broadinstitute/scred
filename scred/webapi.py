"""
scred/webapi.py

Creates the request-sending class used to interact with a REDCap instance.
"""

import requests


class RedcapRequester:
    def __init__(self, url, token, default_format = "json"):
        self._url = url
        self.payloader = self._build_payloader(token, default_format)

    @staticmethod
    def _build_payloader(token, default_format):
        def payloader(**kwargs):
            """Constructs the payload for a request."""
            payload = {
                "token": token,
                "format": default_format,
            }
            payload.update(kwargs)
            return payload
        return payloader

    @property
    def url(self):
        return self._url

    def post(self, **kwargs):
        payload = self.payloader(**kwargs)
        response = requests.post(self.url, payload)
        if not response.ok:
            msg = (
                "Couldn't complete request. Code "
                f"{response.status_code}: {response.reason}."
            )
            raise requests.HTTPError(msg)
        else:
            return response

    def get_metadata(self):
        return self.post(content="metadata").json()

    def get_version(self):
        return self.post(content="version").text
    
    def get_export_fieldnames(self):
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
        return self.post(content="exportFieldNames").json()
