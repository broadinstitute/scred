# scred
Simple python implementation of the REDCap API.

Originally built for REDCap 8.5.28.

If contributing, make sure you're pulling from the `develop` branch!

Not implemented yet:

-Supertokens to manage multiple projects

-Configurable missingness codes

-Non-metadata project attributes, e.g. version

-Data Access Groups

-Basically everything involving data going *into* REDCap instead of *out*

# Basic use
```python
import scred

redcap_token = "mytoken" # store/load your token securely! Just an example!
redcap_url = "https://redcap.fake.example.com/api/"
primary_idvar = "participant_id" # change to match your project

# Set up project; get records; get data dictionary
myproject = scred.RedcapProject(url=redcap_url, token=redcap_token)
records_json = myproject.get_records()
records = scred.RecordSet(records_json, primary_key=primary_idvar)
datadict = myproject.metadata # needed to distinguish N/A from true missing;
records.fill_missing(datadict) # both are blank in REDCap
```

# Specifying records and fields
```python
myproject = scred.RedcapProject(url=redcap_url, token=redcap_token)
# Pass kwargs to use any supported API features
records_json = myproject.get_records(
    records=[1, 7, 9, 23, 55, 80],
    fields=["identifier", "height_cm", "weight_kg", "heart_bpm"],
    filterLogic="age > 22 and age <= 65",
    dateRangeBegin="2019-01-01 00:00:00",
)
```