"""
scred/config.py

Used to manage the user's credentials for REDCap API.
"""

import json
import warnings
from pathlib import Path

# ---------------------------------------------------

CONFIG_FILE_EXAMPLE = "config.json.example"
CONFIG_FILE = "config.json"
SOURCE_DIR = Path(__file__).parent.resolve()

DEFAULT_SETTINGS = {
    "url": "https://redcap.partners.org/redcap/api/",
    "default_format": "json",
}

class RedcapConfig(dict):
    def __init__(self, input_: dict):
        for k, v in input_.items():
            self[k] = v

    def config_is_default(self):
        return self['token'] == "~YourREDCapTokenGoesHere"


def _load_config_from_file_fallback(filename: str = CONFIG_FILE):
    """If config can't be loaded, explicitly check the directory this file is in.
    """
    fallbackdir = SOURCE_DIR # absolute path
    default_location = fallbackdir / filename
    with open(default_location) as cfg_file:
        return json.loads(cfg_file.read())


def load_config_from_file(filename: str = CONFIG_FILE):
    """Load a config from a file.
    """
    print(f"loading file '{filename}'...")
    try:
        with open(SOURCE_DIR / filename) as cfg_file:
            file_content = json.loads(cfg_file.read())
    except FileNotFoundError as ex:
        print(f"Caught FileNotFoundError: {ex}. Falling back to default option.",
        "Make sure you set up your config file and have it in the correct folder.")
        file_content = _load_config_from_file_fallback(filename)
    return RedcapConfig(file_content)
        
try:
    TEST_CFG = load_config_from_file(CONFIG_FILE_EXAMPLE)
    USER_CFG = load_config_from_file(CONFIG_FILE)
    if USER_CFG.config_is_default():
        warnings.warn("DEV: Running default config. Cannot establish real connection.")
except FileNotFoundError:
    # Won't be there if installed from pypi unless manually placed
    TEST_CFG = None
    USER_CFG = None
