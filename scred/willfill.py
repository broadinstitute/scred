import re

def make_redcap_pythonic(astr):
    bouncebacks = [None, ""]
    if astr in bouncebacks:
        return ""

    # make list of all checkbox vars in branching_logic string
    #    NOTE: items in list have the same serialization (ordering) 
    #    as in the string.
    checkbox_snoop = re.findall('\[[a-z0-9_]*\([0-9]*\)\]', astr)
    
    # if there are entries in checkbox_snoop
    if len(checkbox_snoop) > 0:
        # serially replace "[mycheckboxvar(888)]" syntax of each
        # checkbox var in the logic string with the appropraite
        # "record['mycheckboxvar___888']" syntax
        for item in checkbox_snoop:
            
            item = re.sub('\)\]', '\']', item)
            item = re.sub('\(', '___', item)
            item = re.sub('\[', 'record[\'', item)
            
            astr = re.sub('\[[a-z0-9_]*\([0-9]*\)\]', item, astr)
            
        # mask "<=" and ">=" operators to avoid complications when "="
        # is replaced with "=="
        astr = re.sub('<=', 'Z11Z', astr)
        astr = re.sub('>=', 'X11X', astr)
        
        # replace "=" with "=="
        astr = re.sub('=', '==', astr)
        
        # unmask LEQ and GEQ and replace
        astr = re.sub('Z11Z', '<=', astr)
        astr = re.sub('X11X', '>=', astr)
        
        # replace "<>" with "!="
        astr = re.sub('<>', '!=', astr)
    else:
        
        # all basically the same as above, but runs when there are no
        # checkbox vars in the logic
        astr = re.sub('<=', 'Z11Z', astr)
        astr = re.sub('>=', 'X11X', astr)
        astr = re.sub('=', '==', astr)
        astr = re.sub('Z11Z', '<=', astr)
        astr = re.sub('X11X', '>=', astr)
        astr = re.sub('<>', '!=', astr)
        astr = re.sub('\[', 'record[\'', astr)
        astr = re.sub('\]', '\']', astr)
    
    # return the string
    return astr
