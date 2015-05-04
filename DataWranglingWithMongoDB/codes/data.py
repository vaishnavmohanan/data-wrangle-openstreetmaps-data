import xml.etree.cElementTree as ET
import codecs
import pprint
import json
import re
import audit #local *.py file
import os
#Set the proper current working directory
os.getcwd()
os.chdir('C:/Users/vaishnav/Desktop/DataWranglingWithMongoDB')


lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

CREATED = ["version", "changeset", "timestamp", "user", "uid"]


def get_pos(element):
    """Returns the latitude and longitude of the element in an array."""
    lat = float(element.attrib['lat'])
    lon = float(element.attrib['lon'])
    pos = [lat, lon]
    return pos


def ignoring(k):
    """Returns True if key k should be ignored."""
    KEYS = ['ele', 'import_uuid', 'source', 'wikipedia']
    PREFIXES = ['gnis:', 'is_in', 'nhd-s']
    if k in KEYS or k[:5] in PREFIXES:
        return True
    return False


def fix_postcode(v):
    """
    Reduces postcodes to 5 digit strings. Some zips take the form
    'NC12345' or '12345-6789' hindering MongoDB aggregations.
    """
    postcode = ''
    for char in v:
        if char.isdigit():
            postcode += char
        if len(postcode) == 5:
            break
    return postcode
                    

def node_update_k(node, value, tag):
    """Adds 'k' and 'v' values from tag as new key:value pair to node."""
    k = value
    v = tag.attrib['v']                       
    if k.startswith('addr:'):
        # Ignore 'addr:street:' keys with 2 colons
        if k.count(':') == 1:
            if 'address' not in node:
                node['address'] = {}
            if k == 'addr:postcode' and len(v) > 5:
                v = fix_postcode(v)
            # Fix all substrings of street names using a
            # more generalized update method from audit.py
            elif k == 'addr:street':
                v = audit.update(v, audit.mapping)
            node['address'][k[5:]] = v
    # Check for highway exit number nodes
    elif k == 'ref' and node['type'] == 'node':
        node['exit_number'] = v
    # Check for 'k' values that equal the string 'type'
    # which would overwrite previously written node['type']
    elif k == 'type':
        node['service_type'] = v
    # Process other k:v pairs normally
    else:
        node[k] = v
    return node


def process_tiger(node, value, tag):
    """
    Adds a Tiger GPS value ('tiger:__') from the tag as a new
    key:value pair to node['address']
    """
    name_segments = ['name_type', 'name_base', 'name_direction_prefix', 
                     'name_direction_suffix', 'name_direction_suffix_1']
    k = value[6:]  # the substring following 'tiger:'
    v = tag.attrib['v']
    if 'address' not in node:
        node['address'] = {}           
    if 'name' in node:
        node['address']['street'] = node['name']
    elif k == 'zip_left':
        node['address']['postcode'] = v
    elif k in name_segments:
        if 'street' not in node['address']:
            node['address']['street'] = {k:'' for k in name_segments}
        elif isinstance(node['address']['street'], dict):
            node['address']['street'][k] = v
    return node


def join_segments(s):
    """
    Joins 'tiger:__' street name substring values (prefix, base,
    type, suffix) in dict s to a string
    """
    for segment in s:
        if segment in audit.mapping:
            s[segment] = audit.mapping[segment]
    ordered = [ s['name_direction_prefix'], s['name_base'],
                s['name_type'], s['name_direction_suffix'],
                s['name_direction_suffix_1'] ]
    segments = [s for s in ordered if s]
    return ' '.join(segments)


def shape_element(element):
    """
    Takes an XML tag as input and returns a cleaned and reshaped
    dictionary for JSON ouput. If the element contains an abbreviated
    street name, it returns with an updated full street name.
    """
    node = {}
    if element.tag == "node" or element.tag == "way" :
        node['type'] = element.tag
        node['created'] = {}
        if 'lat' in element.attrib:
            # Get coordinates
            node['pos'] = get_pos(element)
        # Begin iterating over subtags
        for tag in element.iter():
            for key, value in tag.items():
                if key in CREATED:
                    node['created'][key] = value
                # Check for problem characters and ignored values
                # in second-level tag 'k' attribute
                elif key == 'k' and not re.search(problemchars, value):
                    if not ignoring(value):
                        if value.startswith('tiger:'):
                            node = process_tiger(node, value, tag)
                        else:
                            node = node_update_k(node, value, tag)
                # Create/update array 'node_refs'
                elif key == 'ref':
                    if 'node_refs' not in node:
                        node['node_refs'] = []
                    node['node_refs'].append(value)
                # Process remaining tags
                elif key not in ['v', 'lat', 'lon']:
                    node[key] = value
        if 'address' in node and 'street' in node['address']:
            if isinstance(node['address']['street'], dict):
                # Replace saved dict of street name segments with full street name
                node['address']['street'] = join_segments(node['address']['street'])
        # Safe to clear() now that element has been processed
        element.clear()
        return node
    else:
        return None


def process_map(file_in, pretty = False):
    """
    Outputs a JSON file with the above structure.
    Returns the data as a list of dictionaries.
    If running main_test(), comment out all array 'data' operations.
    """
    file_out = "{0}.json".format(file_in)
    #data = []
    with codecs.open(file_out, "w") as fo:
        parser = ET.iterparse(file_in)
        for __, elem in parser:
            el = shape_element(elem)
            if el:
                #data.append(el)
                # Output to JSON
                if pretty:
                    fo.write(json.dumps(el, indent=2)+"\n")
                else:
                    fo.write(json.dumps(el) + "\n")
        del parser
    #return data


def main_test():
    data = process_map('charlotte_north-carolina.osm', False)
    #print len(data)
    print 'Map processed'
    
if __name__ == '__main__':
    main_test()
    
'''
I ran len(data)just to know the number of unique nodes and ways.
len(data) = 2781952
'''
