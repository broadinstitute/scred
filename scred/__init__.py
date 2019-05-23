# Load config here?

# import config
# some_path = some/stuff/here
# way_to_load = whatever
# USER_CFG = config.load_config(some_path, way_to_load)
print("DEV: Importing `scred` package")

# Put all public-facing stuff here
from .project import RedcapProject
from .dtypes import Record, RecordSet, DataDictionary
from .config import RedcapConfig
from .webapi import RedcapRequester
