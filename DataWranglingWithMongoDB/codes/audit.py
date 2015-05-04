from collections import defaultdict
import xml.etree.cElementTree as ET
import pprint
import re
import os

os.getcwd()#get the current working directory
os.chdir('C:/Users/vaishnav/Desktop/DataWranglingWithMongoDB')#change the directory to this location


street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
expected = ["Street", "Avenue", "Boulevard", "Drive",
            "Court", "Place", "Square", "Lane", "Road",
            "Trail", "Parkway", "Commons", "Cirle",
            "Cove", "Highway", "Park", "Way", "South"]

# This variable will reflect the changes required in the charlotte_north-carolina.osm file
mapping = { "E": "East",
            "W": "West",
            "N": "North",
            "S": "South",
            "Rd": "Road",
            "Rd.": "Road",
            "ln": "Lane",
            "ln.": "Lane",
            "Ln": "Lane",
            "Ln.": "Lane",
            "Dr": "Drive",
            "Dr.": "Drive",
            "St": "Street",
            "St.": "Street",
            "Ste": "Suite",
            "Ste.": "Suite",
            "Cir": "Circle",
            "Ave": "Avenue",
            "Ave.": "Avenue",
            "Hwy": "Highway",
            "Hwy.": "Highway",
            "Pky": "Parkway",
            "Pky.": "Parkway",
            "Fwy": "Freeway",
            "Fwy.": "Freeway",
            "Blvd": "Boulevard",
            "Blvd.": "Boulevard"
            }


def audit_street_type(street_types, street_name):
    
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected: # if a particular street_name is found problematic it is added to street_types 
            street_types[street_type].add(street_name)


def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")


def audit(osmfile):
    """
    Returns a list of problematic street type values
    for use with the update() name mapping.
    """
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    parser = ET.iterparse(osm_file, events=("start",))
    for event, elem in parser:
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
        # Safe to clear() now that descendants have been accessed
        elem.clear()
    del parser
    return street_types


def update(name, mapping):
    """
    Implemented in data.py
    Updates ALL substrings in string 'name' to
    their values in dictionary 'mapping'
    """
    words = name.split()
    for w in range(len(words)):
        if words[w] in mapping:
            if words[w-1].lower() not in ['suite', 'ste.', 'ste']: # For example, don't update 'Suite E' to 'Suite East'
                words[w] = mapping[words[w]]
    name = " ".join(words)
    return name

# EXPERIMENTAL UNUSED METHOD
# Opted not to use in data.py over the more generalized
# and more optimal 'update()' method above
def update_name(name, mapping):
    """
    If the last substring of string 'name' is an int,
    updates all substrings in 'name', else updates
    only the last substring.
    """
    m = street_type_re.search(name)
    m = m.group()
    # Fix all substrings in an address ending with a number.
    # Example: 'S Tryon St Ste 105' to 'South Tryon Street Suite 105'
    try:
        __ = int(m)
        words = name.split()[:-1]
        for w in range(len(words)):
            if words[w] in mapping:
                words[w] = mapping[words[w]]
        words.append(m)
        address = " ".join(words)
        return address
    # Otherwise, fix only the last substring in the address
    # Example: 'This St.' to 'This Street'
    except ValueError:        
        i = name.index(m)
        if m in mapping:
            name = name[:i] + mapping[m]
    return name


def main_test():
    st_types = audit("charlotte_north-carolina.osm")
    
    pprint.pprint(dict(st_types))
    for st_type, ways in st_types.iteritems():
        for name in ways:
            better_name = update(name, mapping)
            print name, "=>", better_name
            if name == "West Stanly St.":
                assert better_name == "West Stanly Street"
            if name == "S Tryon St Ste 105":
                assert better_name == "South Tryon Street Suite 105"

if __name__ == '__main__':
    main_test()
    
''' Result of my code is:
{'105': set(['S Tryon St Ste 105']),
 '108': set(['Dobys Bridge Road #108']),
 '200': set(['Hwy. 200']),
 '4b': set(['Sardis Road North Ste 4b']),
 'Ardsley': set(['Ardsley']),
 'Ave': set(['Camden Ave', 'Oakland Ave']),
 'Ave.': set(['1900 Selwyn Ave.', '2001 Selwyn Ave.']),
 'B-101': set(['Gilead Road Suite B-101']),
 'Blvd': set(['Blythe Blvd',
              'Carowinds Blvd',
              'East Independence Blvd',
              'South Blvd',
              'University Blvd']),
 'C': set(['East Jefferson Street Ste C']),
 'Cir': set(['Fieldcrest Cir']),
 'Circle': set(['Choate Circle',
                'Deruyter Circle',
                'Granite Circle',
                'Memorial Circle',
                "President's Circle"]),
 'Dr': set(['Crownpoint Executive Dr',
            'Green Birch Dr',
            'Interstate North Dr']),
 'East': set(['East']),
 'Hwy': set(['Black Hwy', 'E. Alexander Love Hwy']),
 'Ln': set(['Virginia Pine Ln']),
 'NE': set(['LePhillip Ct NE']),
 'North': set(['Sardis Road North', 'Union Street North']),
 'Pky': set(['Matthews Township Pky']),
 'Rd': set(['10352 Park Rd',
            'Browne Rd',
            'Celanese Rd',
            'Crestdale Rd',
            'Devinney Rd',
            'Monroe Rd',
            'Old Statesville Rd',
            'Park Rd',
            'Pineville-Matthews Rd',
            'Weddington-Monroe Rd',
            'West Arrowood Rd']),
 'Rd,': set(['Weddington Rd,']),
 'Rd.': set(['Old York Rd.', 'South New Hope Rd.', 'West Sugar Creek Rd.']),
 'SW': set(['Trestle Ct. SW']),
 'St': set(['E Black St', 'Lincoln St', 'OConnell St', 'W 9th St']),
 'St.': set(['West Stanly St.']),
 'W': set(['Hwy 24 27 W']),
 'West': set(['Reese Boulevard West'])}
Virginia Pine Ln => Virginia Pine Lane
Reese Boulevard West => Reese Boulevard West
West Stanly St. => West Stanly Street
Pineville-Matthews Rd => Pineville-Matthews Road
Browne Rd => Browne Road
Devinney Rd => Devinney Road
West Arrowood Rd => West Arrowood Road
10352 Park Rd => 10352 Park Road
Park Rd => Park Road
Celanese Rd => Celanese Road
Monroe Rd => Monroe Road
Weddington-Monroe Rd => Weddington-Monroe Road
Old Statesville Rd => Old Statesville Road
Crestdale Rd => Crestdale Road
Weddington Rd, => Weddington Rd,
President's Circle => President's Circle
Memorial Circle => Memorial Circle
Granite Circle => Granite Circle
Choate Circle => Choate Circle
Deruyter Circle => Deruyter Circle
Old York Rd. => Old York Road
South New Hope Rd. => South New Hope Road
West Sugar Creek Rd. => West Sugar Creek Road
East => East
Sardis Road North => Sardis Road North
Union Street North => Union Street North
LePhillip Ct NE => LePhillip Ct NE
Ardsley => Ardsley
E. Alexander Love Hwy => E. Alexander Love Highway
Black Hwy => Black Highway
Interstate North Dr => Interstate North Drive
Crownpoint Executive Dr => Crownpoint Executive Drive
Green Birch Dr => Green Birch Drive
Hwy. 200 => Highway 200
East Jefferson Street Ste C => East Jefferson Street Suite C
2001 Selwyn Ave. => 2001 Selwyn Avenue
1900 Selwyn Ave. => 1900 Selwyn Avenue
OConnell St => OConnell Street
E Black St => East Black Street
Lincoln St => Lincoln Street
W 9th St => West 9th Street
Fieldcrest Cir => Fieldcrest Circle
Dobys Bridge Road #108 => Dobys Bridge Road #108
Gilead Road Suite B-101 => Gilead Road Suite B-101
Hwy 24 27 W => Highway 24 27 West
S Tryon St Ste 105 => South Tryon Street Suite 105
Matthews Township Pky => Matthews Township Parkway
Trestle Ct. SW => Trestle Ct. SW
Carowinds Blvd => Carowinds Boulevard
University Blvd => University Boulevard
Blythe Blvd => Blythe Boulevard
East Independence Blvd => East Independence Boulevard
South Blvd => South Boulevard
Camden Ave => Camden Avenue
Oakland Ave => Oakland Avenue
Sardis Road North Ste 4b => Sardis Road North Suite 4b
'''
