# Testing scred/webapi.py

import os
import sys
import pytest

sys.path.insert(
    0, os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..')
    )
)

import scred.webapi as webapi
from . import testdata

# ---------------------------------------------------

def test_connection_opens():
    r = webapi.RedcapRequester()

def test_post_method_with_record_params():
    r = webapi.RedcapRequester()
    records_raw = testdata.get_stored_neurogap_record_response()
    # TODO: The line below is slow but should be tested. If we do
    # a split testing setup, this would run on-commit or similar.
    # records = r.post(content="record", data_type="flat").json()


