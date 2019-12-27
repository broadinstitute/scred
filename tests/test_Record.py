# Testing class dtypes.RedcapProject

import os
import sys

import pytest
import pandas as pd

# sys.path.insert(
#     0, os.path.abspath(
#         os.path.join(os.path.dirname(__file__), '..')
#     )
# )

from scred.dtypes import Record, RecordSet, DataDictionary
from . import testdata

def _setup_stored_datadict_and_record():
    stored_datadict = DataDictionary(
        testdata.get_stored_neurogap_metadata_response()
    )
    # stored_record_response has all observations; take 0th so we can
    # work on an individual record instead of a recordset
    stored_record = Record(
        primary_key="subjid",
        data=testdata.get_stored_neurogap_record_response()[0],
    )
    return (stored_datadict, stored_record)

def _setup_stored_datadict_and_recordset():
    stored_datadict = DataDictionary(
        testdata.get_stored_neurogap_metadata_response()
    )
    stored_recordset = RecordSet(
        primary_key="subjid",
        records=testdata.get_stored_neurogap_record_response(),
    )
    return (stored_datadict, stored_recordset)

# ---------------------------------------------------

def test_create_Record_from_fake_data():
    record_data = testdata.get_fake_record_dict()
    record = Record(primary_key="idvar", data=record_data)
    assert record.id == "ABC12345678"
    assert record.loc["Var1", "response"] == False
    assert record.loc["Var10", "response"] == 1
    with pytest.raises(KeyError):
        record.loc["VarNotReal", "response"]


def test_record_transfers_logic_to_exported_checkbox_variables():
    stored_datadict, stored_record = _setup_stored_datadict_and_record()
    stored_record.add_branching_logic(stored_datadict)
    reclogic = stored_record.loc[
        "lec_new_q1___1", "branching_logic"
    ]
    baselogic = stored_datadict.loc[
        "lec_new_q1", "branching_logic"
    ]
    assert reclogic == baselogic


def test_record_backfill_na_values_with_practice_data():
    stored_datadict, stored_record = _setup_stored_datadict_and_record()
    stored_record.add_branching_logic(stored_datadict)
    stored_record._fill_na_values(stored_datadict)
    assert stored_record.loc["psychosis_primary", "response"] == ""
    assert stored_record.loc["is_case", "response"] == '0'
    assert stored_record.loc["organic_cause_other", "response"] == -555


def test_record_backfill_missing_values_with_practice_data():
    stored_datadict, stored_record = _setup_stored_datadict_and_record()
    stored_record.add_branching_logic(stored_datadict)
    stored_record._fill_na_values(stored_datadict)
    stored_record._fill_bad_data()
    assert stored_record.loc["psychosis_primary", "response"] == -444
    assert stored_record.loc["is_case", "response"] == '0'
    assert stored_record.loc["organic_cause_other", "response"] == -555

def test_record_fill_bad_data_raises_error_if_not_nafilled():
    stored_datadict, stored_record = _setup_stored_datadict_and_record()
    stored_record.add_branching_logic(stored_datadict)
    with pytest.raises(AttributeError):
        stored_record._fill_bad_data()


def test_record_fill_missing_converts_to_numeric():
    stored_datadict, stored_record = _setup_stored_datadict_and_record()
    stored_record.add_branching_logic(stored_datadict)
    assert stored_record.loc["is_case", "response"] == '0'
    stored_record.fill_missing(stored_datadict)
    assert stored_record.rcvalue("is_case") == 0


# ===================================================
# Testing class dtypes.RecordSet

def test_create_empty_RecordSet_raises_TypeError():
    with pytest.raises(TypeError):
        RecordSet()

        
def test_create_RecordSet_from_practice_data():
    stored_recordset = RecordSet(
        records=testdata.get_stored_neurogap_record_response(),
        primary_key="subjid",
    )


def test_RecordSet_fill_missing_with_practice_data():
    stored_datadict, stored_recordset = _setup_stored_datadict_and_recordset()
    stored_recordset.fill_missing(stored_datadict)
    # TODO: Add assertions. Currently just proves it will run


@pytest.mark.skip(reason="RecordSet.as_dataframe() not yet implemented")
def test_RecordSet_as_dataframe_returns_DataFrame_with_MultiIndex():
    _, stored_recordset = _setup_stored_datadict_and_recordset()
    df = stored_recordset.as_dataframe()
    assert isinstance(df.index, pd.MultiIndex)
    # assert outer level is ID
    # assert inner level is field_name
    # assert specific record-field responses are as expected
