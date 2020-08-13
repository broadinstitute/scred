"""
conftest.py

Shares objects used by pytest.
"""

import json
import random
from pathlib import Path

import pytest
import requests

import scred
from tests import testdata

random.seed(131002)

# ---------------------------------------------------


@pytest.fixture(scope="session")
def stored_records_json():
    return testdata.get_stored_neurogap_record_response()


@pytest.fixture
def stored_RecordSet_instance(stored_records_json):
    return scred.RecordSet(stored_records_json, "subjid")


@pytest.fixture
def mock_records_response(mock_records_json):
    r = requests.Response()
    r.ok = True
    r.json = lambda x: mock_records_json
    return r


@pytest.fixture(scope="session")
def stored_metadata_json():
    return testdata.get_stored_neurogap_metadata_response()


@pytest.fixture
def stored_DataDictionary_object(stored_metadata_json):
    return scred.DataDictionary(stored_metadata_json)


@pytest.fixture(scope="session")
def stored_efn_json():
    return testdata.get_stored_neurogap_exportFieldNames_response()


@pytest.fixture(scope="session")
def mock_config():
    json_str = Path("scred/config.json").read_text()
    return json.loads(json_str)


@pytest.fixture(scope="session")
def mock_token(mock_config):
    return mock_config["token"]


@pytest.fixture(scope="session")
def mock_url(mock_config):
    return mock_config["url"]


@pytest.fixture
def mock_project(stored_DataDictionary_object):
    faketoken = "ABCD9999DDDDXXZZ067JTP01Y44MSPD1"
    fakeurl = "https://redcap.botulism.org/api/"
    rp = scred.RedcapProject(
        token=faketoken,
        url=fakeurl,
    )
    rp.metadata = stored_DataDictionary_object
    return rp


@pytest.fixture
def mock_ids_clean():
    """Mock REDCap primary IDs that are well-behaved."""
    prefixes = ["ABC", "DEF", "GHJ", "KMN"]
    pref = random.choices(prefixes, k=100)
    nums = [random.randint(10000000, 99999999) for _ in range(0, 100)]
    return [
        z[0] + str(z[1])
        for z in zip(pref, nums)
    ]
