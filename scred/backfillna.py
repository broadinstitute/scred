"""
scred/backfillna.py

Given a scred.Record instance, parses REDCap branching logic (given in pythonic form) to determine whether 
each field prompt was skipped for that record.

There are two reasons values in raw REDCap data can be missing: first, because the question wasn't asked (N/A); 
and second, because the field response is actually blank. REDCap doesn't currently provide a way to distinguish 
between the two, but it is useful to know whether a blank value is expected for a variety of reasons. This module 
uses each field's branching logic to determine whether each field's prompt was presented during collection--that 
is, if a field's logic is satisfied by the record's other field responses. 

To use this module, pass a pandas.DataFrame (or a subclass, e.g. scred.Record) into the Parser class constructor.
This dataframe must contain at least these 2 columns:
    'response': the response provided in REDCap for each field
    'branching_logic': pythonic branching logic (see documentation)

Calling parser.parse() will set the attribute parser.data to a copy of the initial DataFrame; but with a new column,
`LOGIC_MET`, that is only True if the branching logic was satisfied by the record data. This column can be used to
separate the two types of missing values, as implemented in the Record class (see scred/dtypes.py).
"""

import warnings

import pyparsing as pp

# ---------------------------------------------------

global key, operation, value, cond, joint, cond_chain, cond_chain_with_parentheses, logic

# Define elements of parser grammar
key = pp.Word(pp.alphanums + '_')('key') # Variable name: alphanumeric + underscores.
operation = pp.oneOf('> >= == != <= <')('operation') # Comparative operations.
value = pp.Word(pp.nums + '-')('value') # Response value: Negative sign + digits.
cond = pp.Group(key + operation + value)('condition') # Phrase group for a single logical expression.
joint = pp.oneOf('and or') # Phrases that join logical statements together.
cond_chain_with_parentheses = pp.Forward() # Tells parser there may be paren chain coming, inserted by '<<=='
cond_chain = pp.Optional('(') + cond + pp.Optional(')') + pp.Optional(joint + cond_chain_with_parentheses)
cond_chain_with_parentheses <<= cond_chain | '(' + cond_chain + ')' # Inserted at previous pp.Forward()
logic = cond_chain_with_parentheses + pp.StringEnd() # The full grammar

# ---------------------------------------------------
# Set up parse actions.

# Value: convert to numeric
def list_to_ints(list_of_nums):
    """
    Receives a list of nums because <fill in more when I review pyparsing again>
    """
    # It's ok that this casts to int--RC branching logic doesn't support floats
    return [ int(k) for k in list_of_nums ]

value.setParseAction(list_to_ints)


# Condition: access values & check logic
def check_condition(parsed):
    "Takes in parser result, looks up key(s), and returns bool result of statement."
    parsed = parsed[0] # Only has one result
    # Field names have been replaced with their responses by this point
    condition_pieces = " ".join(
        [ str(x) for x in parsed ]
    )
    try:
        return eval(condition_pieces)
    except (SyntaxError, NameError): 
        return False # Handles blank result from key

cond.setParseAction(check_condition)


def fullparse(expression):
    """
    Takes in an expression and parses it using the full branching logic. This
    attempts to split the string into tokens, put the tokens back together
    in a string with responses instead of field names, and evaluate that string.
    """
    global logic
    try: 
        parsed_expr = logic.parseString(expression)
        parsed_expr = " ".join([str(x) for x in parsed_expr])
        return bool(eval(parsed_expr))
    except KeyError:
        # If condition exists but can't be parsed, assume not met
        print("WARNING! KeyError during Parser.fullparse(), may falsely code as N/A.")
        return False 
    except pp.ParseException:
        # This means there was no logic, so we accept it as met
        return True

# ===================================================

class Parser:
    def __init__(self, data):
        global key, operation, value, cond, joint, cond_chain, cond_chain_with_parentheses, logic
        self.data = data
        self.data["LOGIC_MET"] = "" # Add empty column for logic result
        # Complete parser setup by pointing action at this instance
        key.setParseAction(self.use_key)


    def use_key(self, list_with_key):
        """
        Access a key's value in the instance data.
        """
        k = list_with_key[0]
        try:
            return self.val_from_key(k) 
        except KeyError:
            warnings.warn(f"WARNING: Caught KeyError in Parser.use_key() for {k}")
            return False


    def val_from_key(self, key, data=None):
        """
        Helper function that takes a key, looks that key up in the instance record, then returns its value.
        Not sure how this works with use_key and giving a list and all that, but it does. Should revisit.
        """
        if data == None: 
            data = self.data
        try:
            return data.loc[ key, "response" ]
        # Thrown if dataframe does not contain key (IndexError because of 0th entry in `use_key`)
        except IndexError:
            return None


    def parse_all_logic(self):
        """
        Fill `LOGIC_MET` column for each field in the record, based on other responses in the record.
        """
        temp_df = self.data.copy() # Unsafe to alter original during loop
        for idx, row in self.data.iterrows():
            try:
                truth_value = fullparse(row["branching_logic"])
                temp_df.loc[ idx, "LOGIC_MET" ] = truth_value
            # Thrown if "blank" but caught by parser anyway.
            # TODO: Why does this happen..?
            except AttributeError:
                temp_df.loc[ idx, "LOGIC_MET" ] = True 
        self.data = temp_df
