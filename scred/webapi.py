"""
scred/webapi.py

Creates the request-sending class used to interact with a REDCap instance.
"""

import requests

from . import config
from . import dtypes

user_cfg = config.USER_CFG

# ---------------------------------------------------

class RedcapRequester:
    def __init__(self, cfg: config.RedcapConfig = user_cfg):
        self.url = cfg['url']
        self._payloader = __class__._build_payloader(cfg)
        self._version = None


    @staticmethod
    def _build_payloader(cfg):
        def payloader(**kwargs):
            """Constructs the payload for a request."""
            payload = {
                'token': cfg['token'],
                'url': cfg['url'],
                'format': cfg['default_format'],
            }
            payload.update(kwargs)
            return payload
        return payloader


    def post(self, **kwargs):
        payload = self._payloader(**kwargs)
        response = requests.post(self.url, payload)
        if not response.ok:
            msg = (
                "Couldn't complete request. Code "
                f"{response.status_code}: {response.reason}."
            )
            raise requests.HTTPError(msg)
        else:
            return response


    def get(self, **kwargs):
        payload = self._payloader(**kwargs)
        response = requests.get(self.url, payload)
        if not response.ok:
            msg = (
                "Couldn't complete request. Code "
                f"{response.status_code}: {response.reason}."
            )
            raise requests.HTTPError(msg)
        else:
            return response.json()

    
    @property
    def version(self):
        # Don't make this call unless we need to
        if self._version == None:
            self.version = self.post(content='version')
        return self._version

    @version.setter
    def version(self, value):
        self._version = value

# ---------------------------------------------------
