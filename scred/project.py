"""
scred/project.py

Uses REDCap interface and data types defined in other modules to create more
complex classes. Can't go in `dtypes` module because it relies on the `webapi`
module, which lives "above" `dtypes` in the hierarchy.
"""

from copy import deepcopy
from typing import List, Dict, Optional

import requests

from . import webapi
from . import dtypes
from .utils import chunker

# ---------------------------------------------------


class RedcapProject:
    """
    Main class for top-level interaction. Requires a token and url to create
    requester.
    """
    def __init__(self, url, token, metadata=None, requester_kwargs=None):
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
        """
        API entry point URL for REDCap server hosting the project.
        """
        return self.requester.url

    # Maybe cut down on boilerplate with @lazyload decorator?
    @property
    def metadata(self):
        """
        Property that holds the metadata (Data Dictionary) for this project
        instance.
        """
        if self._metadata is None:
            self._metadata = dtypes.DataDictionary(
                self.requester.get_metadata()
            )
        return self._metadata

    @metadata.setter
    def metadata(self, value):
        if not isinstance(value, (dtypes.DataDictionary, None)):
            raise TypeError("metadata must be None or DataDictionary")
        self._metadata = value

    @property
    def efn(self):
        """
        exportFieldNames for the REDCap project.
        Maps (field in REDCap) -> (List[fields in export])
        """
        if self._efn is None:
            self.efn = self.requester.get_export_fieldnames()
        return self._efn

    @efn.setter  # TODO: Refactor
    def efn(self, value: List[Dict]):
        """
        Creates the map of checkboxes to lists of their exportFieldNames.
        GETS: list of dicts; each has original_name, choice_value, export_name
        SETS: dict of original_name -> list[exported]
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
            export_names = [ d["export_field_name"] for d in relevant ]
            mapping[nm] = export_names
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
        """
        Generic POST wrapper to allow unsupported requests.
        """
        return self.requester.post(**kwargs)

    def cbnames(self, cbvar: str):
        """
        Takes a checkbox variable name and returns all exported field names.
        For example, let field `some_event` have options {-1, 1, 2, 999}:
            >>> myproject.cbnames('some_event')
            ['some_event____1', 'some_event___1', 'some_event___2',
                'some_event___999']
        """
        return self.efn[cbvar]

    def any_endorsed(self, record, checkbox) -> bool:
        """
        Given a `record`, looks to see if any export field for `checkbox` was
        endorsed.
        """
        exports = self.cbnames(checkbox)
        for var in exports:
            checked = record.rcvalue(var)
            if checked:
                assert isinstance(checked, int)
                return True
        return False

    def get_records(self, records=None, chunksize: int = 20, **kwargs):
        """
        Export a set of records from `project`. Optional arguments include:
            -forms (replace spaces with _)
            -dateRangeBegin
            -dateRangeEnd
        For dateRange options, format as YYYY-MM-DD HH:MM:SS. Records retrieved
        are created OR modified within that range, and time boundaries are
        exclusive.
        """
        downloader = RecordsDownloader(
            self.requester, chunksize=chunksize, params=kwargs
        )

        # Here: Room for func that does this/handles chunking, async setup
        # return self.post(**payload, **kwargs).json()


class RecordsDownloader:
    """
    Handles the download of record data from REDCap. Primarily called through
    instances of RedcapProject.
    """
    def __init__(
        self, requester, chunksize: int = 20, params: Optional[dict] = None
    ):
        self.requester = requester
        self.chunksize = chunksize
        if params is None:
            params = dict()
        for p, v in params.items():
            params[p] = requester.sanitize_param(v)  # params same across POSTs
        self.static_payload = {
            "content": "record",
            **params,
        }

    def _iter_records(self, records):
        """
        Iterate over the collection of IDs `records`, yielding blocks of len `chunksize`
        until iterator is exhausted. 
        """
        chunk = deepcopy(records) # avoid mutating passed arg
        while len(chunk) >= self.chunksize:
            yield chunk[:self.chunksize]
            del chunk[:self.chunksize]
        yield chunk

    def fetch_records(self, chunk):
        """
        Downloads records listed in `chunk`, yielding each response's JSON content.
        NOTE: What if they aren't using JSON though? 
        """
        to_retry = list()
        for chunk in self._iter_records(records):
            try:
                yield self.requester.post(self.static_payload, records=chunk).json()
            except requests.HTTPError as ex:
                print(f"[DEV] TODO: Retry this request!\nError: {ex}")
                to_retry.append(chunk) # worry about this after the rest works
                # it.chain(iterator, chunk) (?)
        # TODO not done just brainstorming

        # Remember: This is usually getting called by a project. But not always.
        # I also want to do async eventually, so don't want to return all at once.
        # Could the project also yield, pass this up to user who can init records?
        # NEED to test this!! New territory here, dangerous. Do not erase these
        # 2 lines until there are tests in place!
        # TEST: What if I pass records= as a param also? Which one wins?

test_params = {"fields": ["field1", "field2", "NonExistentField"], "fakeparam": 25}
test_records = ["ABC123", "ABC456", "NonExistentRecord"]
syncer = RecordsDownloader(requester, chunksize=20, test_params)
def mock_sync():
    for content in syncer.fetch_records(test_records):
        instances = dtypes.RecordSet(content, primary_key="subj_id")
    # TODO: Do I want to be able to set up an empty RecordSet? Or combine them easily?
