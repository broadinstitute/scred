"""
textract.py

Tools for extracting text entries directly from REDCap.
"""

import pandas as pd
from requests.exceptions import HTTPError

# ---------------------------------------------------


class Textractor:
    """
    Takes a scred.RedcapProject instance and pulls the values of all text fields.
        project: the instance to use for sending requests
        idfield: the field in that REDCap project to use for labeling records
    """
    def __init__(self, project, idfield: str):
        self.project = project
        self.idfield = idfield
        self.bounded = set()
        # TODO: set Project attrs to None, call API when they're first accessed
    
    @property
    def bounded(self):
        """
        Text fields that aren't "free" text, but bounded in some way. Unique IDs, numerics,
        and so on.
        """
        return self._bounded
    
    @bounded.setter
    def bounded(self, value):
        if not isinstance(value, (set, str)):
            value = set(value) # let any exceptions rise
        self._bounded = value

    @property
    def textfields(self):
        text_mask = (self.metadata["field_type"] == "text")
        return set(self.metadata[text_mask].index)
        
    @property
    def desired(self):
        return sorted(self.textfields - self.bounded)

    def pull_desired(self, **kwargs):
        """
        Extracts all provided values from REDCap for each desired field. Returns a
        JSON object.
        """
        data = self._request_desired(**kwargs)
        df = pd.DataFrame(data)
        df = df.set_index(self.idfield).T
        entries = []
        for field, row in df.iterrows():
            has_text = row.loc[lambda x: x != ""] # .loc might break it, test
            for idfield, value in sorted(has_text.iteritems()):
                new = (field, idfield, value)
                entries.append(new) # Factor out 2nd loop into generator? yield has_text
        return entries

    def _request_desired(self, **kwargs):
        """
        Factored out of `pull_desired` for testability. Returns JSON of REDCap records.
        """
        payload = {"fields": [self.idfield] + self.desired}
        payload.update(kwargs)
        return self.project.get_records(**payload)

    def pull_to_csv(self, filename, *args, **kwargs):
        tups = self.pull_desired(*args, **kwargs)
        df = pd.DataFrame(
            tups,
            columns=["Field", "Participant ID", "Value Reported"]
        )
        df["Action Needed"] = ""
        df.to_csv(filename, index=False)
