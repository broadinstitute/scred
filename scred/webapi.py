"""
scred/webapi.py

Creates the request-sending class used to interact with a REDCap instance.
"""

# 3/27/19: Maybe have calls be methods in RedcapRequester, then merge this
# with dtypes.py? Or have this be just for RedcapRequester (name goes back),
# then put RedcapRequester in a separate module that pulls from both and 
# can be kept separate from them? project.py
# Sounds good right now, see how it looks in the morning. 

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


    def send_post_request(self, **kwargs):
        payload = self._payloader(**kwargs)
        response = requests.post(self.url, payload)
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
            self.version = self.send_post_request(content='version')
        return self._version

    @version.setter
    def version(self, value):
        self._version = value


    # Pattern 1: Methods attached to the class instance



# ---------------------------------------------------

# Pattern 2: Top-level functions taking project as argument
# Update: These are all going to methods of Project, a higher-level
# class that accesses RedcapRequester (or a config) and dtypes
def get_redcap_version(project):
    return project.send_post_request(content='version')


def get_data_dictionary(project, fields = None):
    return project.send_post_request(content='metadata')
