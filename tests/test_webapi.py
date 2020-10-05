# Testing scred/webapi.py

import os
import sys
import json
from pathlib import Path

import pytest

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

import scred.webapi as webapi
from . import testdata

# ---------------------------------------------------


def test_create_requester(mock_url, mock_token):
    r = webapi.RedcapRequester(mock_url, mock_token)
