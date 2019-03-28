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

class RedcapConfig(dict):
    def __init__(self, input_: dict):
        for k, v in input_.items():
            self[k] = v

    def config_is_default(self):
        return self['token'] == "~YourREDCapTokenGoesHere"


def load_config_from_file(filename: str = CONFIG_FILE_EXAMPLE):
    """Load a config from a file."""
    print(f"loading file '{filename}'...")
    try:
        # Load cfg data and get map of config instances 
        with open(filename) as cfg_file:
            file_content = json.loads(cfg_file.read())
            return RedcapConfig(file_content)
    except FileNotFoundError as ex:
        print(f"Caught FileNotFoundError: {ex}")
        print("Make sure you set up your config file and have it in the correct folder.")


TEST_CFG = load_config_from_file(CONFIG_FILE_EXAMPLE)
USER_CFG = load_config_from_file(CONFIG_FILE)

if USER_CFG.config_is_default():
    warnings.warn("DEV: Running default config. Cannot establish real connection.")
