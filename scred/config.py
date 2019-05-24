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


def _load_config_from_file_fallback(filename: str = CONFIG_FILE):
    """If config can't be loaded, explicitly check the directory this file is in.
    """
    fallbackdir = SOURCE_DIR # absolute path
    default_location = fallbackdir / filename
    try:
        with open(default_location) as cfg_file:
            return json.loads(cfg_file.read())
    except FileNotFoundError:
        warnings.warn("Could not find a valid config.json in package directory")


def load_config_from_file(filename: str = CONFIG_FILE):
    """Load a config from a file. Should contain:
        url: requests will point to this for API calls
        token: valid 32-character REDCap token
        default_format: REDCap returns this unless other `format` given
    """
    try:
        with open(filename) as cfg_file:
            file_content = json.loads(cfg_file.read())
    except FileNotFoundError as ex:
        file_content = _load_config_from_file_fallback(filename)
        msg = (f"Caught FileNotFoundError: {filename}. Falling back to default option.",
        "Make sure you set up your config file and have it in the correct folder.")
        warnings.warn(msg)
    return RedcapConfig(file_content)


# ===================================================

# Mostly just to make local tests work at this point. Consider tossing whole "config.json
# in the scred package" thing and have users load from a file on their machine with
# credentials before they init the Project.
try:
    TEST_CFG = load_config_from_file(CONFIG_FILE_EXAMPLE)
    USER_CFG = load_config_from_file(CONFIG_FILE)
except FileNotFoundError:
    # Won't be there if installed from pypi unless manually placed
    TEST_CFG = None
    USER_CFG = None
