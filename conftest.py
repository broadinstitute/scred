"""
conftest.py

Shares objects used by pytest.
"""

import json
from pathlib import Path

import pytest
import requests

# ---------------------------------------------------

@pytest.fixture
def mock_records_json():
    from tests import testdata
    return testdata.get_stored_neurogap_record_response()

@pytest.fixture
def mock_records_response(mock_records_json):
    r = requests.Response()
    r.ok = True
    r.json = lambda x: mock_records_json
    return r

@pytest.fixture(scope="session")
def mock_config():
    json_str = Path("scred/config.json.example").read_text()
    return json.loads(json_str)

@pytest.fixture(scope="session")
def mock_token(mock_config):
    return mock_config["token"]

@pytest.fixture(scope="session")
def mock_url(mock_config):
    return mock_config["url"]
