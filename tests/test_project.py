# Testing class project.RedcapProject

import os
import sys

import pytest
import pandas as pd

sys.path.insert(
    0, os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..')
    )
)

from scred import RedcapProject
from scred.config import TEST_CFG
from . import testdata

# ---------------------------------------------------

def test_RedcapProject_init_with_empty_args_uses_stored_user_cfg():
    rp = RedcapProject()


def test_RedcapProject_init_with_token_str():
    faketoken = "ABCD9999DDDDXXZZ067JTP01Y44MSPD1"
    fakeurl = "https://redcap.botulism.org/api/"
    rp = RedcapProject(
        token=faketoken,
        url=fakeurl,
    )
