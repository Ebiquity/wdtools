""" data and functions to map between wikidata types (e.g., Q5) and their common english names (e.g., human)

Here are the standard Spacy types, their brief desctipisons and a
simple mapping to a WD type (may need to be checked and refined

PERSON:'People, including fictional';Q5;
NORP:'Nationalities or religious or political groups';Q15642541;
FAC:'Buildings, airports, highways, bridges, etc';Q13226383;
ORG:'Companies, agencies, institutions, etc';Q43229;
GPE:'Countries, cities, states';Q56061;
LOC:'Non-GPE locations, mountain ranges, bodies of water';Q35145263;
PRODUCT:'Objects, vehicles, foods, etc. (Not services.)';Q2424752;
EVENT:'Named hurricanes, battles, wars, sports events, etc';Q1656682,Q1190554;
WORK_OF_ART:'Titles of books, songs, etc';Q17537576;
LAW:'Named documents made into laws';Q740464;
LANGUAGE:'Any named language';Q33742;
DATE:'Absolute or relative dates or periods';Q205892;
TIME:'Times smaller than a day';Q18640;
PERCENT:'Percentage';Q11229;
MONEY:'Monetary values, including unit';Q1368;
QUANTITY:'Measurements, as of weight or distance';Q47574;
ORDINAL:'first, second, etc';Q923933;
CARDINAL:'Numerals that do not fall under another type';Q11563;

"""

from collections import defaultdict

# dict mapping important high-level WD types to a list of their names
# in WD and other common systems (e.g., Spacy, DBpedia)

wdtype2names = defaultdict(list,
 { 'Q634' : ['planet', 'LOC'],
   'Q2221906' : ['geographic location','LOC'],
  'Q2424752' : ['product', 'PRODUCT'],
  'Q56061' : ['GPE'],
  'Q5' : ['human','PER', 'PERSON'],
  'Q13226383' : ['facility','FAC'],
# 'Q1656682' : ['event', 'EVENT'],
  'Q1190554' : ['occurrence', 'event', 'EVENT'], # covers events and more
  'Q33742' : ['natural language','LANGUAGE'],
  'Q17537576' : ['creative work','WORK_OF_ART'],
  'Q43229' : ['organization','ORG'],
  'Q16334295' : ['group of humans','NORP'],
  'Q7210356' : ['political organisation', 'NORP'],
  'Q191780' : ['ordinal number', 'ORDINAL'],
  'Q21199' :  ['CARDINAL', 'natural number', 'Numerals that do not fall under another type'],
  'Q1368' : ['MONEY', 'Monetary values, including unit'],
  'Q205892' : ['calendar date', 'DATE'],
  'Q573' : ['DATE', 'day'],
  'Q47018901' : ['DATE', 'month'],
  'Q3186692' : ['DATE', 'year', 'calendar year'],
  'Q1248784' : ['airport', 'AIRPORT'],
  'Q4438121' : ['sports organization', 'sports team', 'athletic team'],
  'Q515' :['city'],
  'Q7930989' : ['city'],
  'Q15284' : ['municipality', 'city', 'town', 'village'],
  'Q486972' : ['populated place', 'settlement', 'community'],
  'Q6256' : ['country'],
  'Q42889' : ['vehicle', 'VEH'],
  'Q18643213' : ['military_equipment', 'MIL'],
  'Q728' : ['weapon', 'WEA'],
  'Q4438121' : ['sports organization', 'sports team'],
  'Q216353' : ['title'],
  'Q4164871' : ['position'],
  'Q12737077' : ['occupation', 'profession'],
  'Q223557' : ['physical object', 'physob'],
  'Q61606710' : ['material resource'],  # may be better for physobs
  'Q7184903' : ['abstract object', 'ABSTRACT'],
  'Q3966' : ['computer hardware'],
  'Q7239' : ['organism', 'living thing'],
  'Q729' : ['animal'],
  'Q47461344' : ['written work', 'WRTITTENWORK'],
  'Q14897293' : ['fictional entity', 'fictional', 'FICTIONAL'],
  'Q68': ['computer'],
  'Q4167410' : ['WIKIDISAMBIGUATION'],    #Wikimedia disambiguation page
  'Q740464' : ['LAW', 'law'],
  'Q18640' : ['TIME', 'time'],
  'Q11229' : ['PERCENT', 'percent'],
  'Q35120' : ['ENTITY', 'entity'],
  'Q105815710' : ['performing arts group'],
  'Q1781513': ['positon'], # on a team, e.g. quarterback
  'Q4392985' : ['religious identity','NORP'],
  'Q17379835' : ['Wikimedia page outside the main knowledge tree', 'wikijunk']
 }
)

#TODO: map schema.org types (used by google knowledge graph) to wikidata types)

schematype2names = defaultdict(list, {
  'Action' : [ ],
  'AdministrativeArea' : [], #GPE
  'Animal' : [ ],
  'BodyOfWater' : [ ],   # GPE
  'Book' : [ ], # WORK_OF_ART
  'Brand' : [ ], # PRODUCT
  'BroadcastChannel' : [ ], #ORG
  'CollegeOrUniversity' : [ ], #ORG
  'Corporation' : [ ],  #ORG
  'Country' : [ ], #GPE
  'CreativeWork' : ['WORK_OF_ART'],
  'EducationalOrganization' : [ ], #ORG
  'Event' : ['EVENT'],
  'Intangible' : [ ],
  'MedicalEntity' : [ ],
  'Movie' : [ ],  # WORK_OF_ART
  'MovieTheater' : ['FAC'],
  'MusicAlbum' : [ ], # WORK_OF_ART
  'MusicComposition' : [ ],  #WORK_OF_ART
  'Organization' : ['ORG'],
  'PerformingGroup' : ['ORG'],
  'Periodical' : [ ],  #WORK_OF_ART
  'Person' : ['PER', 'PERSON', 'person'],
  'Place' : ['LOC'],
  'Product' : ['PRODUCT'],
  'ProductModel' : ['PRODUCT'],
  "RadioStation": [ ], #ORG
  'RiverBodyOfWater' : ['GPE'],
  'Religion' : ['NORP'],
  'SoftwareApplication' : ['PRODUCT'],
  'SportsOrganization' : [ ], #ORG
  'SportsTeam' : [ ], #ORG
  'Thing' : [ ],
  'TVSeries' : [ ], # WORK_OF_ART
  'Vehicle' : [ ], #PRODUCT 
  'VideoGame' : [ ] #PRODUCT 
 }
)


spacytype2wdtypes = {
  'PERSON' : ['Q5'],
  'NORP' : ['Q15642541'],
  'FAC' : ['Q13226383'],
  'ORG' : ['Q43229'],
  'GPE' : ['Q56061'],
  'LOC' : ['Q35145263'],
  'PRODUCT' : ['Q2424752'],
  'EVENT' : ['Q1656682', 'Q1190554'],
  'WORK_OF_ART' : ['Q17537576'],
  'LAW' : ['Q740464'],
  'LANGUAGE' : ['Q33742'],
  'DATE' : ['Q205892'],
  'TIME' : ['Q18640'],
  'PERCENT' : ['Q11229'],
  'MONEY' : ['Q1368'],
  'QUANTITY' : ['Q47574'],
  'ORDINAL' : ['Q923933'],
  'CARDINAL' : ['Q11563'],
   'Q7397': ['software']
  }


# cybersecurity-releeant wikidata types from an earlier system --
# needs to be reworked and integrated?

wd_cyber_target = {
  'Q7397': 'software',
  'Q205663': 'process',
  'Q68': 'computer',
  'Q1301371': 'network',
  'Q14001': 'malware',
  'Q783794': 'company',
  'Q161157': 'password',
  'Q1541645': 'process identifier',
  'Q4418000': 'network address',
  'Q5830907': 'computer memory',
  'Q82753': 'computer file',
  'Q2904148': 'information leak',
  'Q4071928': 'cyberattack',
  'Q477202': 'cryptographic hash function',
  'Q141090': 'encryption',
  'Q5227362': 'data theft',
  'Q631425': 'computer vulnerability',
  'Q627226': 'Common Vulnerabilities and Exposures',
  'Q2801262': 'hacker group',
  'Q2798820': 'security hacker',
  'Q8142': 'currency',
  'Q2587068': 'sensitive information',
  'Q3966': 'computer hardware',
  'Q17517': 'mobile phone',
  'Q986008': 'payment system',
  'Q13479982': 'cryptocurrency',
  'Q20826013': 'software version',
  'Q20631656': 'software release',
  'Q44601380': 'property that may violate privacy',
  'Q1058914': 'software company',
  'Q278610': 'Dropper',
  'Q1332289':'black hat',
  'Q2798820':'security hacker',
  'Q22685':'hacktivism',
  'Q47913':'intelligence agency',
  'Q28344495':'computer security consultant',
  'Q26102':'whistleblower',
  'Q317671':'botnet',
  'Q9135':'operating system',
  'Q4825885':'authentication protocol',
  'Q2659904':'government organization',
  'Q1668024':'service on internet',
  'Q202833':'social media',
  'Q870898':'computer security software',
  'Q27096213': ['geographic entity']

}

wd_cyber_ok = {
    'Q5': 'human',
    'Q43229': 'organization',
    'Q82794': 'geographic region',
    'Q1048835': 'political territorial entity'}

# wikidata types that should not be in a search result
wd_cyber_bad = {
  'Q2188189':'musical work',
  'Q4438121':'sports organization',
  'Q11410':'game',
  'Q14897293':'fictional entity',
  'Q32178211':'music organisation',
  'Q16010345':'performer',
  'Q483501':'artist',
  'Q56678558':'unknown composer author',
  'Q28555911':'ordinary matter'
}

# -------------------------- mapping a type name (e.g., PER) to a wikidata type (e.g., Q5) or schema.org type (e.g., Person)

    
# dict maping a type name to its corresponding WD type.  We also map a type to
# itself, so it given a string X that might be either a WD type or a spacy type
# or some of ther type, name2wdtype[X] should always return the WD type.

name2wdtypes = defaultdict(list)

# populate the name2wdtypes dictionary
for atype, names in wdtype2names.items():
    name2wdtypes[atype] = [atype]
    for name in names:
        name2wdtypes[name].append(atype)

# dict maping a type name to its corresponding schema.org type.  We also map a type to
# itself, so it given a string X that might be either a schema.org type or a spacy type
# or some of ther type, names2schematype[X] should always return the WD type.

names2schematypes = defaultdict(list)

# populate the names2schematypes dictionary
for atype, names in schematype2names.items():
    names2schematypes[atype] = [atype]
    for name in names:
        names2schematypes[name].append(atype)
        
# a funtion that might be useful to go from a common name for a type
# to it's corresponding Wikidata types

def wd_types(type_names):
    """ given a type name or list of type names, returns a list of wd_types """
    if type(type_names) != list:
        if type(type_names) == str:
            type_names = [type_names]
        elif type(type_names) == set:
            type_names = list(type_names)
        else:
            print(f"classes nust be a string, set or list: {type_names}")
            return []
    wd_types = set()  #use set in case of duplicates
    for name in type_names:
        if type(name) == str and name[0] == 'Q':
             # we assume this is a wd type
             wd_types.add(name)
        else:
            if name not in name2wdtypes:
                print(f"ERROR: unrecognized type name {name}")
            for t in name2wdtypes[name]:
                wd_types.add(t)
    return(list(wd_types))

# --------------------------------------------------------------------------
# SCALE 2021 type lists (under development)
# --------------------------------------------------------------------------


# these are all of the types that we might want to be aware of for scale2021
scale_types = wdtype2names.keys()

# the default target type if none is specified
scale_default_target_types = ['ENTITY']

# These are types that should be ok and useful for scale2021
scale_default_ok_types =  [

#person or organization (Q106559804)
 'ENTITY',
 'AIRPORT',
 'CARDINAL',
# 'DATE',
 'EVENT',
 'FAC',
 'GPE',
 'LANGUAGE',
 'LAW',
 'LOC',
 'MIL',
 'MONEY',
 'NORP',
 # 'ORDINAL',
 'ORG',
 'PER',
 # 'PERCENT',
 'PRODUCT',
# 'QUANTITY',
 # 'TIME',
 'VEH',
 'WEA']

# These are types that will probably not be useful for scale2021.  We will need to add more
scale_default_bad_types = [
    'wikijunk',
    'WIKIDISAMBIGUATION',
    'FICTIONAL',
#     'WRTITTENWORK',
#     'WORK_OF_ART',
#     'performing arts group'
    ]

