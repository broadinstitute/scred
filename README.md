# scred
Simple python implementation of the REDCap API.

Originally built for REDCap 8.5.28.

If contributing, make sure you're pulling from the `develop` branch!

Not implemented yet:

-Supertokens to manage multiple projects

-Data Access Groups

-Basically everything involving stuff going *into* REDCap instead of *out*

**MOCK USE**
```python
import scred

redcap_token = "mytoken" # store/load your token securely! Just an example!
redcap_url = "https://redcap.fake.example.com/api/"
primary_idvar = "participant_id" # change to match your project

# Set up project; get records; get data dictionary
project = scred.RedcapProject(token=redcap_token, url=redcap_url)
records = scred.RecordSet(
    records=project.post(content="record").json(),
    id_key=primary_idvar
)
datadict = scred.DataDictionary(
    project.post(content="metadata").json()
)

# Fill in N/A vs. True Missing (codes not yet configurable)
records.fill_missing(datadict)
```
