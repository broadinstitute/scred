# Testing scred/textract.py

import os
import sys
import pytest

sys.path.insert(
    0, os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..')
    )
)

import scred.textract as txr
from testdata import MockProject

def _mock_request():
    pass # TODO: Mock `requests` response

# ---------------------------------------------------

def test_create_textractor_with_mock_project():
    mock_project = MockProject()

def test_placeholder():
    pass
