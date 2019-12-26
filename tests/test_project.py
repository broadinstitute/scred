# Testing class project.RedcapProject

import os
import sys

import pytest
import pandas as pd

# sys.path.insert(
#     0, os.path.abspath(
#         os.path.join(os.path.dirname(__file__), '..')
#     )
# )

from scred import RedcapProject, DataDictionary
from . import testdata

# ---------------------------------------------------

def test_RedcapProject_init_with_token_and_url():
    faketoken = "ABCD9999DDDDXXZZ067JTP01Y44MSPD1"
    fakeurl = "https://redcap.botulism.org/api/"
    rp = RedcapProject(
        token=faketoken,
        url=fakeurl,
    )

def test_cbnames_returns_exports_for_existing_field(stored_metadata_json, stored_efn_json):
    faketoken = "ABCD9999DDDDXXZZ067JTP01Y44MSPD1"
    fakeurl = "https://redcap.botulism.org/api/"
    rp = RedcapProject(
        token=faketoken,
        url=fakeurl,
    )
    rp.metadata = DataDictionary(stored_metadata_json)
    rp.efn = stored_efn_json
    assert "lec_q1___1" in rp.cbnames("lec_q1")

def test_any_endorsed_returns_False_if_none_endorsed(
    stored_RecordSet_instance,
    stored_metadata_json,
    stored_efn_json,
    ):
    faketoken = "ABCD9999DDDDXXZZ067JTP01Y44MSPD1"
    fakeurl = "https://redcap.botulism.org/api/"
    rp = RedcapProject(
        token=faketoken,
        url=fakeurl,
    )
    rp.metadata = DataDictionary(stored_metadata_json)
    rp.efn = stored_efn_json
    testrec = stored_RecordSet_instance["1"]
    assert not rp.any_endorsed(testrec, "lec_new_q1")
    assert rp.any_endorsed(testrec, "lec_q1") # move to separate test
