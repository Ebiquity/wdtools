"""

Search Wikidata to find entities given a string and optional sets of types. Returns a ranked list of
objects, one for each hit, with basic information from Wikidata and optionally DBpedia in one or
more languages. An example of a call from the command line:

  python wd_search.py "UMBC" --types ORG --oktypes LOC FAC --badtypes 'sports team' --lang en zh --dbpedia --limit 20 --top 5

Types can be any wikidata type (e.g., Q5 for human) or a type name in entity_types.py.  The search prefers hits with a type in --types but will accept ones with a type in --oktypes.  If an entity has a type in --badtypes, it is rejected. The --limit parameter defines how many initial candidates are checked (up to 50) and --top says how many good hits are returned.  The --lang args are 2-letter codes for language-specific information.  If the --dbpedia flag is given, the additional information from dbpedia is included (types and an abstract paragraph of text).  --no-dbpedia suppresses this.

The return value is a list, roughly ordered from best to worst match.

"""

import argparse as ap
import sys
import json
from SPARQLWrapper import SPARQLWrapper, JSON
import requests
from collections import defaultdict
from datetime import datetime
from entity_types import *  #fixme

DEFAULT_LANG = ['en']
#DEFAULT_LANG = ['en', 'fa', 'ru', 'zh']

def get_args(PD):
    # PD is s profile of defaults, typically either DF or DFS
    p = ap.ArgumentParser()
    p.add_argument('string', help='string to search for in label, alias or text')
    p.add_argument('-l', '--lang', nargs='+', default=PD['langs'], help='return string data in these 2-letter language codes, defaults to just en' )
    p.add_argument('--top', nargs='?', type=int, default=PD['top'], help='number of ranked hits to return, defaults to 2')
    p.add_argument('--limit', nargs='?', type=int, default=PD['limit'], help='number of initial candidates to find, defaults to 25')
    p.add_argument('-t', '--types', nargs='+', default=PD['target_types'], help='must be one of these types, defaults to Q35120 (entity)')
    p.add_argument('-b', '--badtypes', nargs='+', default=PD['bad_types'], help='must no be one of these types, defaults to none')
    p.add_argument('-ok', '--oktypes', nargs='+', default=PD['ok_types'], help='use of one of these types if not enough with target types, defaults to none')        
    p.add_argument('-o', '--out', nargs='?', type=ap.FileType('wb'), default=sys.stdout, help='file for output (defaults to stdout)')
    p.add_argument('--dbpedia', dest='dbpedia', nargs=1, default=PD['dbpedia'], help='get DBpdia abstract and types (default)')
#    p.add_argument('--no-adbpedia', dest='dbpedia', action='store_false', help='do not get DBpdia information')
    p.add_argument('--category', dest='category', nargs='?', default=PD['category'], help='one of all, strictinstance, instance, strictconcept, or concept. Defaults to all.')
   # p.set_defaults(PD['dbpedia'])
    args = p.parse_args()
    return args

# profiles are dictionary of default values for wd_search parameters

DF = {
 'langs' : ['en'],
 'target_types' : ['Q35120'], # 
 'ok_types' : [],
 'bad_types' : [],  # written work
 'limit' : 20,
 'top' : 2,
 'dbpedia' : True,
 'category' : 'all' }

# A profile of defauts for hltcoe scale 2021
DFS = {
 'langs' : ['en', 'ru', 'zh', 'fa'],
 'target_types' : scale_default_target_types, 
 'ok_types' : scale_default_ok_types,
 'bad_types' : scale_default_bad_types,
 'limit' : 20,
 'top' : 1,
 'dbpedia' : False,
 'category' : 'all' }

# for performance tracking, these will be incremented for each query
wd_queries = 0
dbp_queries = 0
candidates_checked = 0

# sparql endpoint
default_wd_endpoint = "https://query.wikidata.org/bigdata/namespace/wdq/sparql"
default_dbpedia_endpoint = "http://dbpedia.org/sparql"

# user agent for http request (required by wikidata query service) change name as appropriate
USER_AGENT = "SearchBot/2.0 (Tim Finin)"

def link(string, target_types=DF['target_types'], ok_types=DF['ok_types'], bad_types=DF['bad_types'], category=DF['category']):
    """ return the top hit. default type is 'entity' """
    #print('linking', string)
    result = wd_search(string, target_types=target_types, ok_types=ok_types, bad_types=bad_types, dbpedia=False, top=1, category=category)
    return result[0] if result else None

# special version for scale 2021 project
def scale_link(string, target_types=DFS['target_types'], ok_types=DFS['ok_types'], bad_types=DFS['bad_types'], category=DFS['category']):
    """ return the top hit. default type is 'entity' """
    #print('linking', string)
    result = wd_scale_search(string, target_types=target_types, ok_types=ok_types, bad_types=bad_types, dbpedia=False, top=1, category=category)
    return result[0] if result else None


# search wikidata given a string for entities, filter by requiring a
# type on the target or ok list and no types on the bad list

def wd_search(string, langs=DF['langs'], target_types=DF['target_types'], ok_types=DF['ok_types'], bad_types=DF['bad_types'], limit=DF['limit'], top=DF['top'], dbpedia=DF['dbpedia'], category=DF['category']):
    """ generic WD search """
    #print(f"wdsearch string:{string}, langs:{langs}, target_types:{target_types}, ok_types:{ok_types}, bad_types:{bad_types}, limit:{limit}, top:{top}, dbpedia={dbpedia}, category:{category}")

    # track these for performance reviews
    global wd_queries, dbp_queries, candidates_checked
    wd_queries = dbp_queries = candiates_checked = 0
    #print('wd_search:', category)
    hits = wd_string_search(string, target_types=target_types, ok_types=ok_types, bad_types=bad_types, category=category, limit=limit, top=top)
    return [complete_item(hit, langs, dbpedia) for hit in hits]

# version for HLTCOE scale 2021 project
def wd_scale_search(string, langs=['en','ru','zh','fa'], target_types=DFS['target_types'], ok_types=DFS['ok_types'], bad_types=DFS['bad_types'], limit=DFS['limit'], top=DFS['top'], dbpedia=DFS['dbpedia'], category=DFS['category']):
    #ok_types += scale_types
    # bad_types += ['Q17537576'] # + creative work
    hits = wd_string_search(string, target_types=target_types, ok_types=ok_types, bad_types=bad_types, category=category, limit=limit, top=top)    
    return [complete_item_scale(hit) for hit in hits]

    
def wd_string_search(string, target_types=DF['target_types'], ok_types=DF['ok_types'], bad_types=DF['bad_types'], limit=DF['limit'], top=DF['top'], category=DF['category']):

    """ search for up to limit items whose text matches string that
    returns a list ranked by several factors. We want to return the top
    number of them whose types have a target, preferred, or acceptable type and
    do not also have a bad type.  Ones that have a target type will be ranked highest,
    followed by those with a preferred type, followed by ones with only an
    acceptable type. Within each category items are ranked by their intial order,
    which reflects a matching strategy. """
 
    global candidates_checked

    target_types = wd_types(target_types)
    ok_types = wd_types(ok_types)
    bad_types = wd_types(bad_types)

    if category not in ['all', 'strictinstance', 'instance', 'strictconcept', 'concept']:
        #print('wd_search_string:', category)
        print(f"ERROR: {category} not a recognized category values, should be 'all', 'strictinstance', 'instance', 'strictconcept', or 'concept'")
        return []

    #print(f"search for {top} hit with TARGET:{target_types}, OK:{ok_types}, BAD:{bad_types}")

    target_hits = []  # candidates with a type in target_types and no type in bad_types
    ok_hits = []      # candidates with a type in ok_types and no type in bad_types

    api_url = "https://www.wikidata.org/w/api.php"
    params = {'action':'query', 'list':'search', 'srsearch':string, 'srlimit':limit, 'format':'json'}
    result = requests.Session().get(url=api_url, params=params).json()
    candidates = [item for item in result['query']['search']]
    
    # process each candidate until we've found enough hits
    for item in candidates:
        #print('Checking:', item)
        candidates_checked += 1
        id = item['title']
        found_types = get_types(id, target_types, ok_types, bad_types, category)
        if found_types == ([],[]):
            # found neither a target nor a ok type, skip
            continue
        targ_types, ok_types = found_types
        
        item['types'] = [t[0] + ':' + t[1] for t in targ_types + ok_types ]
        if targ_types:
            target_hits.append(item)
        elif ok_types:
            ok_hits.append(item)
        # stop checking candidates if we have enough hits
        if top and (len(target_hits) >= top):
            break

    # return target hits and enough ok hits needed to get to top or as close as possible
    hits = (target_hits + ok_hits)
    metadata = {'search_string': string, 'target_types': target_types, 'ok_types':ok_types, 'bad_types': bad_types, 'candidates': len(candidates), 'hits': len(hits), 'top': top, 'category': category, 'time':datetime.now().isoformat()}
    #print('metadata', metadata)
    
    if not hits:
        return []
    elif len(hits) > top:
        hits = hits[:top]

    return [{'id':hit['title'], 'types':hit['types'], 'metadata':metadata} for hit in hits]


#todo: we might get the number of statements and sitelinks for possible future work on ranking the hits better
# ?x wikibase:statements ?outcoming .
# ?x wikibase:sitelinks ?sitelinks .
# SERVICE wikibase:label { bd:serviceParam wikibase:language "en" . }

def complete_item(item, langs, dbpedia):
    """ item is a dict with an id property that's a wikidata id. Add
    more useful information in a set of languages and, id dbpedia is
    true, from DBpedia. Returns the dict. """

    #print('completing:', item, langs, dbpedia)
    id = item['id']
    item['wd_uri'] = f"https://www.wikidata.org/wiki/{id}"
    item['immediate_types'] = get_immediate_types_labels(id)
    item['immediate_supertypes'] = get_immediate_supertype_labels(id)
    item['is_instance'] = bool(item['immediate_types'])
    item['is_concept'] = bool(item['immediate_supertypes'])
    item['wikipedia'] = wp_name = get_en_wikipedia_name(id)
    for lang in langs:
        item[lang] = d = {}
        ladw = get_ladw(id, lang)
        #if any(ladw):
        #    d['label'], d['aliases'], d['description'], d['wikiname'] = ladw
        d['label'], d['aliases'], d['description'], d['wikiname'] = ladw
    if dbpedia:
        item['DBpedia_types'] = get_dbpedia_types(id, wp_name)
        for lang, text in get_dbpedia_abstracts(id, langs, wp_name):
            item[lang]['abstract'] = text
    item['metadata']['wd_queries'] = wd_queries
    item['metadata']['dbp_queries'] = dbp_queries
    item['metadata']['candidates_checked'] = dbp_queries    
    return item

# version for HLTCOE scale 2021
def complete_item_scale(item):
    """ item is a dict with an id property that's a wikidata id. Add
    more useful information in a set of languages and, id dbpedia is
    true, from DBpedia. Returns the dict. """

    id = item['id']

    labels = {}
    descriptions = {}
    aliases = {}

    for (lang, lab, al, desc) in get_scale_llads(id):
        labels[lang] = lab
        aliases[lang] = al
        descriptions[lang] = desc

    item['qid'] = id
    item['counts'] = -1
    item['scores'] = [ ]
    item['labels'] = labels
    item['aliases'] = aliases
    item['descriptions'] = descriptions

    #remove unwanted keys
    item.pop('metadata')
    item.pop('types')
    return item

def wikidata_search(string, limit=20):
    # search wikidata for items containing string in their name, alias or description
    # I think the service is limited to 50 results
    limit = min(limit, 50)    
    api_url = "https://www.wikidata.org/w/api.php"
    params = {'action':'query', 'list':'search', 'srsearch':string, 'srlimit':limit, 'format':'json'}
    result = requests.Session().get(url=api_url, params=params).json()
    return [item for item in result['query']['search']]

# Three SPARQL queries to get a wikidata item's type IDs and en labels
# of type covering (1) get both entity and class views, (2) get only
# entity view, (3) get only class view

q_types_labels_query_all = """
select distinct ?type ?typeLabel {{
   wd:{QID} wdt:P31/wdt:P279*|wdt:P279* ?type .
   ?type rdfs:label ?typeLabel .
   FILTER (lang(?typeLabel) = "en") }}"""

q_types_labels_query_instance = """
select distinct ?type ?typeLabel {{ 
   wd:{QID} wdt:P31/wdt:P279* ?type .
   ?type rdfs:label ?typeLabel .
   FILTER (lang(?typeLabel) = "en") }}"""

q_types_labels_query_strictinstance = """
select distinct ?type ?typeLabel {{ 
   wd:{QID} wdt:P31/wdt:P279* ?type .
   FILTER NOT EXISTS {{wd:{QID} wdt:P279 []}}
   ?type rdfs:label ?typeLabel .
   FILTER (lang(?typeLabel) = "en") }}"""

q_types_labels_query_concept = """
select distinct ?type ?typeLabel {{ 
   wd:{QID} wdt:P279* ?type .
   ?type rdfs:label ?typeLabel .
   FILTER (lang(?typeLabel) = "en") }} """

q_types_labels_query_strictconcept = """
select distinct ?type ?typeLabel {{ 
   wd:{QID} wdt:P279* ?type .
   FILTER NOT EXISTS {{wd:{QID} wdt:P31 []}}
   ?type rdfs:label ?typeLabel .
   FILTER (lang(?typeLabel) = "en") }}"""

def get_types(qid, target_types, ok_types, bad_types, category, endpoint=default_wd_endpoint):
    """
    Given a wikidata id (e.g., Q7803487) returns a tuple with its types in target_types, ok_types.
    returns immediaely with ([],[]) if a type in bad_types. We assume that target_types, preferred_types, acceptable_types,
    and bad_types are disjoint.  Each type is represented as a tuple (id, name), e.g., ('Q5', 'human').  If target_types and
    preferred_types are both an empty list or set, all types not in bad_types are considered preferred.

    category should be on of all, instance, strictinstance or, cconcept

    """
    # retrieve types for wd id
    #print("getting types:", qid, target_types, ok_types, bad_types, category)
    #alltypes = not(target_types or preferred_types) or target_types == ['']

    #print('get_types:', category)
    failure = ([ ], [ ])

    if category == 'all':
        query = q_types_labels_query_all.format(QID=qid)
    elif category == 'strictinstance':
        query = q_types_labels_query_strictinstance.format(QID=qid)        
    elif category == 'instance':
        query = q_types_labels_query_instance.format(QID=qid)
    elif category == 'strictconcept':
        query = q_types_labels_query_strictconcept.format(QID=qid)
    elif category == 'concept':
        query = q_types_labels_query_concept.format(QID=qid)
    else:
        print('ERROR: bad category value in get_types', category)
        return failure

    #print(f"\nquery: {query}\n")

    results = query_wd(query, endpoint=endpoint)
    ttypes = set()
    oktypes = set()
    for result in results["results"]["bindings"]:
        id_label = (wd_entity_id(result['type']['value']), result['typeLabel']['value'])
        id = id_label[0]
        if id in bad_types:
            #print(f"{qid} bailinging bad type:{id_label}")
            return failure       
        elif id in target_types:
            ttypes.add(id_label)
        elif id in ok_types:
            oktypes.add(id_label)
    found = (list(ttypes), list(oktypes))
    #print(f"got_types found {found}")
    return (list(ttypes), list(oktypes))

## send query to enpoints

def query_wd(query, endpoint=default_wd_endpoint):
    global wd_queries
    wd_queries += 1
    return query_endpoint(query, endpoint)

def query_dbpedia(query, endpoint=default_dbpedia_endpoint):
    global dbp_queries
    dbp_queries += 1
    return query_endpoint(query, endpoint)
    
def query_endpoint(query, endpoint):
    """ send query to endpoint and return response as JSON """
    sparql = SPARQLWrapper(endpoint, agent=USER_AGENT)
    sparql.setReturnFormat(JSON)
    sparql.setQuery(query)
    return sparql.query().convert()


# SPARQL query to get entity's label, description, aliases and wikiname for a language
q_ladw_query = """
SELECT DISTINCT ?label ?desc (group_concat(distinct ?alias; separator='|') as ?aliases) ?wname
WHERE {{
  OPTIONAL {{wd:{QID} rdfs:label ?label. FILTER(lang(?label) = "{LANG}") }}
  OPTIONAL {{wd:{QID} skos:altLabel ?alias. FILTER(lang(?alias) = "{LANG}") }}
  OPTIONAL {{wd:{QID} schema:description ?desc. FILTER(lang(?desc) = "{LANG}") }}
  OPTIONAL {{?article schema:about wd:{QID}; schema:inLanguage "{LANG}"; schema:name ?wname ;
    schema:isPartOf <https://{LANG}.wikipedia.org/> .
  FILTER (!CONTAINS(?wname, ':')) }}
  }}
GROUP BY  ?label ?desc ?wname """


def get_ladw(id, lang):
    """ Given a Wikidata id, returns a tuple of the item's label, aliases, description, and wikiname for a language"""
    results = query_wd(q_ladw_query.format(QID=id, LANG=lang))
    if results:
        rs = results["results"]["bindings"][0]
        label = rs['label']['value'] if 'label' in rs else ''
        aliases = rs['aliases']['value'].split('|') if 'aliases' in rs else []
        aliases = [] if aliases == [''] else aliases
        desc = rs['desc']['value'] if 'desc' in rs else ''
        wname = rs['wname']['value'] if 'wname' in rs else '' 
        return (label, aliases, desc, wname)

# SPARQL query to get entity's label, description, and aliases for a language
q_scale_lad_query = """select ?lang ?label ?desc (group_concat(distinct ?alias; separator='|') as ?aliases) {{
  BIND(wd:{QID} as ?id)
  {{BIND("en" as ?lang)
   OPTIONAL {{?id rdfs:label ?label . FILTER(lang(?label) = ?lang)}}
   OPTIONAL {{?id schema:description ?desc . FILTER(lang(?desc) = ?lang)}}
   OPTIONAL {{?id skos:altLabel ?alias . FILTER(lang(?alias) = ?lang)}}}}
  UNION
  {{BIND("ru" as ?lang)
   OPTIONAL {{?id rdfs:label ?label . FILTER(lang(?label) = ?lang)}}
   OPTIONAL {{?id schema:description ?desc . FILTER(lang(?desc) = ?lang)}}
   OPTIONAL {{?id skos:altLabel ?alias . FILTER(lang(?alias) = ?lang)}}}}
  UNION
  {{BIND("zh" as ?lang)
   OPTIONAL {{?id rdfs:label ?label . FILTER(lang(?label) = ?lang)}}
   OPTIONAL {{?id schema:description ?desc . FILTER(lang(?desc) = ?lang)}}
   OPTIONAL {{?id skos:altLabel ?alias . FILTER(lang(?alias) = ?lang)}}}}
  UNION
  {{BIND("fa" as ?lang)
   OPTIONAL {{?id rdfs:label ?label . FILTER(lang(?label) = ?lang)}}
   OPTIONAL {{?id schema:description ?desc . FILTER(lang(?desc) = ?lang)}}
   OPTIONAL {{?id skos:altLabel ?alias . FILTER(lang(?alias) = ?lang)}}}}
}}
GROUP BY ?lang ?label ?desc """

def get_scale_llads(id):
    """ Given a Wikidata id (e.g Q42), returns a list of tuple of item's language, label, aliases, and description for en, ru, zh and fa"""
    results = query_wd(q_scale_lad_query.format(QID=id))
    llads = []
    if results:
        for r in results["results"]["bindings"]:
            lang = r['lang']['value']
            label = r['label']['value'] if 'label' in r else ''
            aliases = r['aliases']['value'].split('|') if 'aliases' in r else [ ]
            aliases = [ ] if aliases == [''] else aliases
            desc = r['desc']['value'] if 'desc' in r else ''
            llads.append((lang, label, aliases, desc))
    return llads
        
def get_immediate_types_labels(id):
    """ Returns a set of the id's immediate types and immediate supertypes"""
#    q = f'select ?class ?classLabel where {{wd:{id} wdt:P31 ?class. SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en".}}}}'
    q = f"select ?class ?label {{wd:{id} wdt:P31 ?class. ?class rdfs:label ?label. FILTER (lang(?label) = 'en') }}"
    result =  query_wd(q)
    class_labels = set()
    for x in result['results']['bindings']:
        class_labels.add(x['class']['value'].split('/')[-1] + ':' +  x['label']['value'])
    return list(class_labels)

def get_immediate_supertype_labels(id):
    """ id should be a class. Returns a set of the id's immediate supertypes """
    q = f"select ?class ?label {{wd:{id} wdt:P279 ?class. ?class rdfs:label ?label. FILTER (lang(?label) = 'en') }}"
    result =  query_wd(q)
    class_labels = set()
    for x in result['results']['bindings']:
        class_labels.add((x['class']['value'].split('/')[-1] + ':' + x['label']['value']))
    return list(class_labels)


def get_en_wikipedia_name(qid):
    """ Given a wikidata QID, get its en Wikipedia name if it has one, else '' """
    query = f'SELECT ?name {{?art schema:about wd:{qid}; schema:inLanguage "en"; schema:name ?name; schema:isPartOf <https://en.wikipedia.org/>.}} LIMIT 1'
    results = query_wd(query)
    if results["results"]["bindings"]:
        return results["results"]["bindings"][0]['name']['value'].replace(' ', '_')
    else:
        return ''

def get_dbpedia_abstracts(qid, langs=['en'], name=''):
    """ Get DBpedia abstract from wikidata qid in given languages, returning '' when not available """
    if not name:
        name = get_en_wikipedia_name(qid)
        if not name: return ''  # exit with '' if no name
    name = encode_string(name)
    slangs = ','.join([quote_str(l) for l in langs])
    query = f'select distinct ?lang ?text where {{dbr:{name} dbo:abstract ?text. BIND(lang(?text) AS ?lang) FILTER(?lang IN ({slangs})) }}'
    results = query_dbpedia(query)
    return [(binding['lang']['value'], binding['text']['value']) for  binding in results["results"]["bindings"]]

def quote_str(s): return "'"+s+"'"

def get_dbpedia_types(qid, name=''):
    """ returns a list of dbpedia types given qid, a wikidata id """
    if not name:
        name = get_en_wikipedia_name(qid)
        # exit with [] if still no en wikipedia name
        if not name: return []
    #print(f"getting dbpeditypes for {qid}, {name} ")
    query = f"select distinct ?t where {{dbr:{encode_string(name)} rdf:type/rdfs:subClassOf* ?t }}"
    #print(query)
    results = query_dbpedia(query)["results"]["bindings"]
    dbp_types = []
    for dbp_type in [binding['t']['value'] for binding in results]:
        if dbp_type.startswith("http://dbpedia.org/ontology/"):
            dbp_types.append('dbo:' + dbp_type[28:])
        elif dbp_type.startswith("http://umbel.org/umbel/rc/"):
            dbp_types.append('umbel:' + dbp_type[26:])            
    #print(f"Foynd {dbp_types}")
    return dbp_types

def remove_prefix(text, prefix):
    return text[len(prefix):] if text.startswith(prefix) else text
    
def get_isinstance_istype(id):
    """ Returns a tuple of two Booleans idicating if id is an instance and is a type """
    q = f"""select distinct ?instance ?type where {{
          BIND (exists {{wd:{id} wdt:P31 []}} AS ?instance) 
          BIND (exists {{wd:{id} wdt:P279 []}} AS ?type) }}"""
    results = query_wd(q)
    bindings = results["results"]["bindings"][0]
    return (bindings['instance']['value'], bindings['type']['value'])

def isa_type(id):
    """ returns True iff id is a wikidata type, i.e., has an instance, a subtype or a supertype """
    return query_wd(f"ASK {{?x wdt:P31|wdt:P279|^wdt:P279 wd:{id} }}")['boolean']

def isa_instance(id):
    """ returns True iff id isa wikidata instance """
    return query_wd(f"ASK {{wd:{id} wdt:P31 ?x}}")['boolean']

def wd_entity_id(url):
    """ returns entity id if url is an entity, else the url"""
    return url.split('http://www.wikidata.org/entity/')[1] if url.startswith('http://www.wikidata.org/entity/') else url

def encode_string(text):
    """ prefix some chars with a backslash for using in a sparql query """
    for ch in """(),'/@""" :
        if ch in text:
            text = text.replace(ch,"\\"+ch)
    #text = text.replace('(','\(').replace(')','\)').replace(',','\,').replace("'","\\'").replace('/','\/').replace('@','\@')
    if text.endswith('.'):
        text = text[:-1] + '\.'
    return text

def hits_string(hits):
    return json.dumps(hits, separators=(',',':'), indent=2, ensure_ascii=False, sort_keys=True)

def summary(hits):
    """ returns a short summary with just the QID, name and description """
    def summary1(hit):
        if hit: return (hit['id'], hit['en']['label'], hit['en']['description'])
    if type(hits) == list:
        return [summary1(h) for h in hits]
    elif hits:
        return summary1(hits)
    else:
        return 'No match'

# special version for scale
def scale_summary(hits):
    """ returns a short summary with just the QID, name and description """
    def summary1(hit):
        if hit: return (hit['qid'], hit['labels']['en'], hit['descriptions']['en'])
    if type(hits) == list:
        return [summary1(h) for h in hits]
    elif hits:
        return summary1(hits)
    else:
        return 'No match'
    

def main(args):
    result = wd_scale_search(args.string, langs=args.lang, limit=args.limit, target_types=args.types, ok_types=args.oktypes, bad_types=args.badtypes, top=args.top, dbpedia=args.dbpedia, category=args.category)
    with args.out as out:
        out.write(hits_string(result))
        out.write('\n')

if __name__ == '__main__':
    main(get_args(DFS))


