# dtypes.py

# Defines classes whose instances represent various REDCap responses

import re
from typing import Collection

import pandas as pd

# ---------------------------------------------------

# TODO: Make this configurable, not everyone uses our ID scheme
# Maybe set it somewhere in config so it can be overwritten for
# a project? Default to None, and only check if not None?
ID_TEMPLATE = re.compile(r"[A-Z]{3}[1-9][0-9]{7}")

class DataDictionary:
    pass


class DataAccessGroup:
    pass


class Record(pd.DataFrame):
    """
    Represents a single observation in a REDCap project.
    """
    def __init__(self, id_key: str, data: dict = dict()):
        """
        REDCap API will present a list of dicts; each dict is one record. We create a
        record from a response dict and can handle bulk pulls with loops/RecordSet.
        """
        print("Creating a record instance...")
        self._id = data[id_key]
        super().__init__(data)
    
    @property
    def id(self):
        return self._id
    
    @id.setter
    def id(self, value):
        # Confirm the subject ID at least looks real
        if not ID_TEMPLATE.match(value):
            raise ValueError(f"Invalid ID: {value}")
        self._id = value


class RecordSet(pd.DataFrame):
    def __init__(self, records: Collection[Record]):
        """
        Use the record IDs to build an Index.
        """
        # will this work if r.index is also multi?
        idx = pd.MultiIndex([ (r.id, r.index) for r in records ])
        # Make data a property..?
        self._data = pd.DataFrame(index=idx)



# breakthrough note: chained indexing problem is all about __getitem__.
# so it's really about making sure assignment is directly calling __setitem__
# on the object and never trusting what's returned to be a view or copy.

# Implications for how I treat the .copy() method too. Probably don't need to
# do that nearly as often as I am.
