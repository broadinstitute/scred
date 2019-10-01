# Testing class dtypes.DataDictionary

import os
import sys
import pytest

sys.path.insert(
    0, os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..')
    )
)

import pandas as pd

from scred.dtypes import DataDictionary
from . import testdata

# Duplicate of a function below to remove boilerplate. Always starting
# with a fresh copy of our fake API response
def _setup_testdata_DataDictionary():
    ddraw = testdata.get_fake_datadict_response()
    return DataDictionary(ddraw)

def _setup_neurogap_practice_DataDictionary():
    return DataDictionary(
        testdata.get_stored_neurogap_datadictionary_response()
    )

# ---------------------------------------------------

def test_create_DataDictionary_from_test_data():
    ddraw = testdata.get_fake_datadict_response()
    dd = DataDictionary(ddraw)


def test_access_DataDictionary_branching_logic_with_testdata():
    dd = _setup_testdata_DataDictionary()
    logic = dd["branching_logic"]


def test_DataDictionary_instance_is_subclass_of_pandas_DataFrame():
    import pandas as pd
    dd = _setup_testdata_DataDictionary()
    assert issubclass(dd.__class__, pd.DataFrame)


def test_DataDictionary_has_field_name_as_index():
    dd = _setup_testdata_DataDictionary()
    assert dd.index.name == "field_name"


def test_make_redcap_pythonic_converts_syntax():
    dd = _setup_neurogap_practice_DataDictionary()
    dd.make_logic_pythonic()
    var_and_logic = {
        "ubacc_q1_t4": "ubacc_score_t1 < 20 and ubacc_score_t2 < 20 and ubacc_score_t3 < 20",
        "ken_ethn_1": "(birth_country == 2) and (ethnicity_number == 1 or ethnicity_number == 2 or ethnicity_number == 3 or ethnicity_number == 4 or ethnicity_number == 5)",
        "ken_lang_2": "current_country == 2 and (lang_number >= 2)",
        "pat_lang_sa_1": "current_country == 1 and (pat_langs_num == 1 or pat_langs_num == 2 or pat_langs_num == 3 or pat_langs_num == 4)",
        "hypomania_psq3": "hypomania_psq2 == 0 and hypomania_psq1 == 1",
        "assist_other_specify_amt": "assist_other_specify_list___1 == 1 or assist_other_specify_list___2 == 1 or assist_other_specify_list___3 == 1",
    }
    for field, expected in var_and_logic.items():
        assert dd.loc[field, "branching_logic"] == expected
