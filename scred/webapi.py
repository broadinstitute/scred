"""
scred/webapi.py

Creates the request-sending class used to interact with a REDCap instance.
"""

import requests

from .utils import LogMixin


class RedcapRequester(LogMixin):
    """
    Wrapper for `requests` API that handles web calls to/from REDCap.
    """

    def __init__(self, url, token, default_format="json"):
        self.logger.debug("[DEV] Testing LogMixIn")
        print(
            f"[DEV@{__file__}.{self.__class__}] "
            f"Check for Testing LogMixIn message!"
        )
        self._url = url
        self.payloader = self._build_payloader(token, default_format)

    @staticmethod
    def _build_payloader(token, default_format):
        """
        Lock in the REDCap user token and format to avoid passing each time.
        kwargs are inserted at the end; you can overwrite on a given request.
        """

        def payloader(**kwargs):
            """Constructs the payload for a request."""
            payload = {"token": token, "format": default_format}
            payload.update(kwargs)
            return payload

        return payloader

    @property
    def url(self):
        """
        The API entry point for all requests.
        """
        return self._url

    def post(self, **kwargs):
        """
        Wraps around `requests.post` to handle request URL and authorization.
        """
        params = {k: self.sanitize_param(v) for k, v in kwargs.items()}
        payload = self.payloader(params)
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
        """
        Returns JSON metadata for this project from the host REDCap server.
        """
        return self.post(content="metadata").json()

    def get_version(self):
        """
        Returns the version of REDCap running on the project's server.
        """
        return self.post(content="version").text

    def get_export_fieldnames(self):
        """ (From REDCap documentation)
        This method returns a list of the export/import-specific version of
        field names for all fields (or for one field, if desired) in a project.
        This is mostly used for checkbox fields because during data exports and
        data imports, checkbox fields have a different variable name used than
        the exact one defined for them in the Online Designer and Data
        Dictionary, in which *each checkbox option* gets represented as its own
        export field name in the following format: field_name + triple
        underscore + converted coded value for the choice. For non-checkbox
        fields, the export field name will be exactly the same as the original
        field name. Note: The following field types will be automatically
        removed from the list returned by this method since they cannot be
        utilized during the data import process: 'calc', 'file', and
        'descriptive'.

        The list that is returned will contain the three following attributes
        for each field/choice: 'original_field_name', 'choice_value', and
        'export_field_name'. The choice_value attribute represents the raw
        coded value for a checkbox choice. For non-checkbox fields, the
        choice_value attribute will always be blank/empty. The
        export_field_name attribute represents the export/import-specific
        version of that field name.
        """
        return self.post(content="exportFieldNames").json()

    @staticmethod
    def sanitize_param(param, sep: str = ",") -> str:
        """
        REDCap's API accepts multiple values for 1 parameter, but not by
        repeating the key like most services. Instead, needs to be in
        one comma-separated string.
        If param is already a string, return it as-is.
        If param is a container, join it on `sep` and return that.
        """
        if not isinstance(param, str):
            return sep.join(param)
        return param
