"""
scred/project.py

Uses REDCap interface and data types defined in other modules to create more complex
classes. Can't go in `dtypes` module because it relies on the `webapi` module, which
lives "above" `dtypes` in the hierarchy.
"""

from typing import List, Dict

from . import webapi
from . import dtypes

# ---------------------------------------------------
   
class RedcapProject:
    """
    Main class for top-level interaction. Requires a token and url to create requester.
    """
    def __init__(self, url, token, metadata = None, requester_kwargs = None):
        if requester_kwargs is None:
            requester_kwargs = dict()
        self.requester = webapi.RedcapRequester(
            token=token,
            url=url,
            **requester_kwargs,
        )
        self._metadata = None
        self._version = None
        self._efn = None

    @property
    def url(self):
        return self.requester.url

    # Maybe cut down on boilerplate with @lazyload decorator? Checks if None, sets if so
    @property
    def metadata(self):
        """
        Property that holds the metadata (Data Dictionary) for this project instance.
        """
        if self._metadata is None:
            self._metadata = dtypes.DataDictionary(self.requester.get_metadata())
        return self._metadata
    
    @metadata.setter
    def metadata(self, value):
        if not isinstance(value, (dtypes.DataDictionary, None)):
            raise TypeError("metadata must be None or DataDictionary")
        self._metadata = value

    @property
    def efn(self):
        if self._efn is None:
            self.efn = self.requester.get_export_fieldnames()
        return self._efn

    @efn.setter # TODO: Refactor
    def efn(self, value: List[Dict]):
        """
        Creates the map of checkboxes to lists of their exportFieldNames.
        HAVE: list of dicts; each dict has original_name, choice_value, export_name
        WANT: dict of original_name -> list[exported]
        """
        mapping = dict()
        differing = [
            d for d in value
            if d["original_field_name"] != d["export_field_name"]
        ]
        names = [ d["original_field_name"] for d in differing ]
        names = set(names)
        for nm in names:
            relevant = [ d for d in differing if d["original_field_name"] == nm ]
            exports = [ d["export_field_name"] for d in relevant ]
            mapping[nm] = exports
        self._efn = mapping

    @property
    def version(self):
        if self._version is None:
            self._version = self.requester.get_version()
        return self._version

    @version.setter
    def version(self, value):
        self._version = value

    def post(self, **kwargs):
        return self.requester.post(**kwargs)
    
    def cbnames(self, cbvar: str):
        """
        Takes a checkbox variable name and returns all exported field names. For example,
        let field `some_event` have options {-1, 1, 2, 999}:
            >>> myproject.cbnames('some_event')
            ['some_event____1', 'some_event___1', 'some_event___2', 'some_event___999']
        """
        return self.efn[cbvar]
        
    def get_records(self, records = None, fields = None, **kwargs):
        """
        Export a set of records from the given project. Optional arguments also include:
            -forms (replace spaces with _)
            -dateRangeBegin
            -dateRangeEnd
        For dateRange options, format as YYYY-MM-DD HH:MM:SS. Records retrieved are created
        OR modified within that range, and time boundaries are exclusive.
        """
        payload = {"content": "record"}
        if records and not isinstance(records, str):
            records = ",".join(records)
        payload.update(records=records)
        if fields and not isinstance(fields, str):
            fields = ",".join(fields)
        payload.update(fields=fields)
        return self.post(**payload, **kwargs).json()

    def any_endorsed(self, record, checkbox) -> bool:
        """
        Given a `record`, looks to see if any export field for `checkbox` was endorsed.
        """
        exports = self.cbnames(checkbox)
        for var in exports:
            checked = record.rcvalue(var)
            if checked:
                assert isinstance(checked, int)
                return True
        return False

    # def was_asked(self, record, variable: str) -> bool:
    #     """
    #     Uses project metadata to see if observation `record` satisfied the branching logic
    #     for field `variable`.
    #     """
    #     meta = self.metadata
    #     assert meta.blogic_fmt == "python"
    #     logic = meta.loc[variable, "branching_logic"]
    #     parser = dtypes.backfillna.Parser(record)
