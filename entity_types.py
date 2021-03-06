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

# dict mapping important high-level Wikidata types to a list of their names
# in WD and other common systems (e.g., Spacy, DBpedia)

wdtype2names = defaultdict(list,
 {
  'Q105815710' : ['performing arts group'],
  'Q10856962' : ['anthroponym', 'NAME'],
  'Q11229' : ['percent'],
  'Q1190554' : ['occurrence', 'EVENT'], # covers events and more
  'Q12143' : ['time zone', 'timeZone'],
  'Q1248784' : ['airport'],
  'Q12737077' : ['occupation', 'profession'],
  'Q13226383' : ['facility','FAC'],
  'Q1368' : ['MONEY', 'Monetary values, including unit'],
  'Q14897293' : ['fictional entity', 'fictional'],
  'Q15284' : ['municipality', 'city', 'town', 'village'],
  'Q16334295' : ['group of humans'],
  'Q1656682' : ['event', 'EVENT'],
  'Q17379835' : ['Wikimedia page outside the main knowledge tree', 'wikijunk'],
  'Q17537576' : ['creative work','WORK_OF_ART'],
  'Q1781513': ['positon'], # on a team, e.g. quarterback
  'Q18640' : ['TIME', 'time'],
  'Q18643213' : ['military_equipment', 'MIL'],
  'Q191067' : ['ARTICLE'],
  'Q191780' : ['ordinal number', 'ORDINAL'],
  'Q205892' : ['calendar date', 'DATE'],
  'Q21199' :  ['CARDINAL', 'natural number', 'Numerals that do not fall under another type'],
  'Q216353' : ['title'],
  'Q2188189' : ['song', 'SONG'],
  'Q2221906' : ['geographic location','LOC'],
  'Q231002' : ['nationality', 'NORP'],
  'Q223557' : ['physical object', 'physob'],
  'Q2424752' : ['product', 'PRODUCT'],
  'Q3186692' : ['DATE', 'year', 'calendar year'],
  'Q33742' : ['natural language','LANGUAGE'],
  'Q35120' : ['ENTITY', 'entity'],
  'Q3966' : ['computer hardware'],
  'Q41710' : ['ethnic group', 'NORP'],
  'Q4164871' : ['position'],
  'Q4167410' : ['WIKIDISAMBIGUATION'],    #Wikimedia disambiguation page
  'Q42889' : ['vehicle', 'VEH'],
  'Q43229' : ['organization','ORG'],
  'Q4392985' : ['religious identity','NORP'],
  'Q4438121' : ['sports organization', 'sports team', 'athletic team'],
  'Q4438121' : ['sports organization', 'sports team'],
  'Q47018901' : ['DATE', 'month'],
  'Q47461344' : ['written work', 'WRTITTENWORK'],
  'Q486972' : ['populated place', 'settlement', 'community'],
  'Q5' : ['human','PER', 'PERSON'],
  'Q515' :['city'],
  'Q56061' : ['GPE'],
  'Q573' : ['DATE', 'day'],
  'Q61606710' : ['material resource'],  # may be better for physobs
  'Q6256' : ['country'],
  'Q634' : ['planet', 'LOC'],
  'Q68': ['computer'],
  'Q7184903' : ['abstract object', 'ABSTRACT'],
  'Q7278' : ['political party', 'NORP'],
  'Q7239' : ['organism', 'living thing'],
  'Q728' : ['weapon', 'WEA'],
  'Q729' : ['animal'],
  'Q732577': ['PUBLICATION'],
  'Q740464' : ['LAW', 'law'],
  'Q7406919' :['service', 'ORG', 'ORGANIZATION'],
  'Q7930989' : ['city'],
  # procure related good types
  'Q199897' : ['Medical Subject Headings', 'MeSHterm', 'MESH'],
  'Q18123741' : ['infectious disease'],
  'Q12136' : ['disease'],
  'Q15712714' : ['biomolecular structure'],
  'Q8054' : ['protein'],                      
  'Q11173' : ['chemical compound'],
  'Q16521' : ['taxon'],
  'Q7108' : ['biotechnology'],
  'Q7187' : ['gene'], 
  'Q855769' : ['strain'], # as in a strin of virus or bacteria
  'Q796194' : ['medical procedure'],
  'Q2826767' : ['disease causative agent'],
  'Q105259234' : ['immunization safety'],
  'Q30612' : ['clinical trial'],
  'Q105967696' : ['vaccine type'],
  'Q47103999' : ['type of statistic'],
   # properties
  'P6099' : ['clinical trial phase'],
  'P7153' : ['significant place'],
  'P3098' : ['ClinicalTrials.gov ID'],
  'P585' : ['point in time'],
  'Q19887775' : ['Wikidata property related to medicine'],
  'Q22988603' : ['Wikidata property related to biology'],
  # procure related BAD types
  # 'Q1792379' : ['art genre'],
  'Q483394' : ['genre'],  
  'Q106043376': ['music release type', 'MUSIC'],
  'Q4438121' : ['sports organization']
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
  'RadioStation': [ ], #ORG
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
  'Q7397': ['software'],
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

def add_unique(dictionary, name, atype):
    # add atype to the dictionary for name and name.lower if it's not already in it
    if atype not in dictionary[name]:
        dictionary[name].append(atype)
    name = name.lower()
    if atype not in dictionary[name]:
        dictionary[name].append(atype)    

# populate the name2wdtypes dictionary, addng an entry for each name and its lowercase version
for atype, names in wdtype2names.items():
    add_unique(name2wdtypes, atype, atype)
    for name in names:
        add_unique(name2wdtypes, name, atype)

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


# these are all of the types that we might want to be aware of for scale2021
scale_types = wdtype2names.keys()
