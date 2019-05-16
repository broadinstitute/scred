# backfillna.py
# Contact: Mark Baker (e: mbaker@broad)

# Parses branching logic to fill in the "Not Applicable" values for REDCap.
# Base REDCap functionality doesn't distinguish between values that are missing
# because the question wasn't asked (N/A) and values that are missing due to staff
# error or inability to collect the information (true missing).
# This module uses each field's branching logic to determine whether the question
# was asked--if the logic is satisfied by that record's other fields, it was.

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
# Value: convert to numeric. Condition: access values & check logic.
def list_to_ints(list_of_nums):
    # It's ok that this casts to int--RC branching logic doesn't support floats.
    return [ int(k) for k in list_of_nums ]

value.setParseAction(list_to_ints)


def check_condition(parsed):
    "Takes in parser result, looks up key(s), and returns bool result of statement."
    parsed = parsed[0] # Only has one result
    # Field names have been replaced with their responses by this point
    humpty = " ".join([str(x) for x in parsed])
    try:
        return eval(humpty)
    except (SyntaxError, NameError): 
        return False # Handles NaN result from key

cond.setParseAction(check_condition)


def fullparse(expression):
    """Takes in an expression and parses it using the full logic. This
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
        # Finish up parser by setting actions that refer to the class's instance.
        key.setParseAction(self.use_key)
        
    def use_key(self, list_with_key):
        "Access key's value in instance's data set."
        k = list_with_key[0]
        try:
            return self.val_from_key(k) 
        except KeyError:
            print(f"WARNING: Caught KeyError in Parser.use_key() for {k}")
            return False

    def val_from_key(self, key, data=None):
        """Helper function that takes a key, looks that key up in the instance record, then returns its value.
        Pandas df always wants to return a Series when pulling values, so there's a messy statement requiring 
        a reset of the index to (reliably) pull the 0th entry.
        """
        if data == None: 
            data = self.data
        try:
            return data.loc[ data.VarName==key, "response" ].reset_index(drop=True)[0]
        # Thrown if data frame does not contain that key (IndexError because it
        # tries to take the 0th entry of an empty frame.)
        except IndexError:
            return None

    def parse_all_logic(self):
        temp_df = self.data.copy() # Unsafe to alter original during loop
        # Fill new 'Met' col with bool result of Logic column
        for idx, row in self.data.iterrows():
            try:
                truth_value = fullparse(row["branching_logic"])
                temp_df.loc[ idx, "LOGIC_MET" ] = truth_value
            except AttributeError: # Backup for if no logic to evaluate but caught by parser
                temp_df.loc[ idx, "LOGIC_MET" ] = True 
        self.data = temp_df # Export result to attribute
