"""
tests/mock_use.py

Not a test, just quickly working out how I want to use this eventually.
"""

import scred

# Would also like to be able to skip this and auto-instantiate if no config
# argument is given and only one valid config is there.
config_path = /path/to/cfg/config.json
scred.load_config(config_path)

neuromex = scred.Project.from_config()
# So add a classmethod to call that and give it the current implementation as default
# Do we WANT non-config ways? Maybe I should just have Project() with no args only
# work when there's a single viable config, then allow it to use a path or config file
# to instantiate if either of those are passed as args
neuromex = scred.Project() # I like this better

# ---------------------------------------------------

## Say I'm running a sync...
records = neuromex.get_records() # default is all
dbconn = db.Connect(some_cfg)
reshaped = reshape(records) # user implements reshape
sql_iterable = get_sql_magic(reshaped) # not sure how this is best done
# reshape(d) poses some design challenges but remember that's for the user to
# deal with, not us
dbconn.insert(sql_iterable)

# ---------------------------------------------------

## Writing error checks... Maybe add arg to neuromex.get_records()?
# No, this whole thing should be left to the user. They pull the raw data through this
# API and are on their own (or can use our other packages!) from there. The check should
# operate on the synced data, not happen as it's downloaded

# ---------------------------------------------------

## Writing a function to add a new language
new_langs = {191: "Swahili", 192: "Senegalese"}
dd = neuromex.get_metadata() # returns DataDictionary instance?
lang_fields = [lang_field1, lang_field2, lang_field3]
dd = dd.add_field_response(lang_fields, new_langs)
dbconn.update(
    table="LANGUAGE_LOOKUP", 
    fields=["lang_code", "lang_value"],
    entries=new_langs
)
# This is interesting to think on... What do I want to pass to .update? I should
# keep that in mind and try to make sure you can talk to REDCap like you would
# any other database. If you can pass field name, values, etc. to one you should
# ideally be able to pass it to the other easily.

# The usual way with SQL would be to pass (field1, field2) values (value1, value2)
# but that doesn't let you send multiple entries. So what's the collection equivalent
# of that? Maybe the update I'm doing is the problem here and I need to send those
# as separate statements. That's the user's problem, although we can try to make
# add_field_response more flexible later on. I think for now, the way that makes the 
# most sense in a REDCap context is to pass a list of fields and a map of the new 
# k-v pairs you want to add. Any weird stuff that happens between REDCap and the
# ultimate destination isn't on this package.

# ---------------------------------------------------

## Changing an arbitrary attribute on some Instrument
dd = neuromex.get_metadata()
dd.loc[ dd['form_name'] == "name_of_instrument", "required_field" ] = "y"
neuromex.upload_data_dict(newdd)
