"""
conftest.py

Shares objects used by pytest.
"""

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
    import requests
    r = requests.Response()
    r.ok = True
    r.json = lambda x: mock_records_json
    return r