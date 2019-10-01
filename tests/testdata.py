# Raw responses from REDCap API will come as a list of dicts. Make sure
# the test data we create returns everything in the correct format.

import json

# ---------------------------------------------------

def get_fake_record_dict():
    idx = ["idvar"] + [ f"Var{n}" for n in range(1, 11) ]
    responses = ["ABC12345678", False, 3, "sometimes", 16, 22.5, True, "", -10, "", 1]
    return dict(zip(idx, responses))

def get_fake_datadict_response():
    field_name = ["idvar"] + [ f"Var{n}" for n in range(1, 11) ]
    form_name = ["instr1"]*3 + ["instr2"]*5 + ["instr3"]*3
    branching_logic = [None]*9 + ["Var5 < 20"] + ["Var8 = -10"]
    required_field = ["y"]*7 + [""]*2 + ["y"]*2
    # TODO: Clean this up at some point. Good thing for new person to do.
    # Switch to more complete example and/or NamedTuple so we don't mix up
    # arg positions later.
    dlist = []
    for atuple in zip(field_name, form_name, branching_logic, required_field):
        dlist.append({  
            "field_name": atuple[0],
            "form_name": atuple[1],
            "branching_logic": atuple[2],
            "required_field": atuple[3],
        })
    return dlist

def get_stored_neurogap_record_response():
    # The list of dicts we get from response.json()
    with open("tests/stored_neurogap_practice_records.json", "r") as fp:
        raw = json.load(fp)
    return raw

def get_stored_neurogap_datadictionary_response():
    # The list of dicts we get from response.json()
    with open("tests/stored_neurogap_practice_datadict.json", "r") as fp:
        raw = json.load(fp)
    return raw

def get_stored_neurogap_exportFieldNames_response():
    # The list of dicts we get from response.json()
    with open("tests/stored_neurogap_exportFieldNames.json", "r") as fp:
        raw = json.load(fp)
    return raw

# ---------------------------------------------------

class TestDataResponses:
    def __init__(self):
        self.resps = {
            "record": get_stored_neurogap_record_response(),
        }

testresponses = TestDataResponses()
# use like: recresp = testresponses.resps["record"]
