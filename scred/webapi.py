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
