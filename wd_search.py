"""

Search Wikidata to find entities give a string and optional sets of types. Returns an ranked list of
objects, one for each hit, with basic information from Wikidata and optionally DBpedia in one or
more languages. An example of a call from the command line:

  python wd_search.py "UMBC" --types ORG --oktypes LOC FAC --badtypes 'sports team' --lang en zh --dbpedia --limit 20 --top 5

Types can be any wikidata type (e.g., Q5 for human) or a type name in entity_types.py.  The search prefers hits with a type in --types but will accept onese with a type in --oktypes.  If an entity has a type in --badtypes, it is rejected. The --limit parameter defines how many initial candidates are checked (up to 50) and --top says how many good hits are returned.

The return value is a list, roughly ordered from best to worst match.  For example, searching for 'wannacry' produces two hits:

[ { "id":"Q29957041",
    "uri":"https://www.wikidata.org/wiki/Q29957041",
    "types":["Q4071928:cyberattack"],
    "description":"ransomware cyberattack",
    "label":"WannaCry ransomware attack",
    "aliases":[
      "WanaCrypt0r 2.0",
      "Wanna Decryptor",
      "WannaCry",
      "WannaCrypt",
      "WCry",
      "WannaCry cyberattack" ] },
  { "id":"Q29908721",
    "uri":"https://www.wikidata.org/wiki/Q29908721",
    "types":[ "Q4071928:cyberattack", "Q7397:software", "Q14001:malware"],
    "description":"Ransomware",
    "label":"WannaCry",
    "aliases":[
      "Ransom.Win32.Wannacry",
      "WanaCrypt0r 2.0",
      "Wanna Decryptor",
      "WannaCrypt",
      "WCry" ]  }


s = "President_(government_title)Call this from the command line for experimentation, e.g.:
   python3 wd_search.py <string> <required types>
   python3 wd_search.py Adobe
   python3 wd_search.py python Q7397
   python3 wd_search.py mitre  "Q783794,Q2659904"

"""

import argparse as ap
import sys
import json
from SPARQLWrapper import SPARQLWrapper, JSON
import requests
from collections import defaultdict
import entity_types

DEFAULT_LANG = ['en']
#DEFAULT_LANG = ['en', 'fa', 'ru', 'zh']

def get_args():
    p = ap.ArgumentParser()
    p.add_argument('string', help='string to search for in label, alias or text')
    p.add_argument('-l', '--lang', nargs='+', default=DEFAULT_LANG, help='return string data in these 2-letter language codes, defaults to just en' )
    p.add_argument('--top', nargs='?', type=int, default=2, help='number of ranked hits to return, defaults to 2')
    p.add_argument('--limit', nargs='?', type=int, default=25, help='number of initial candidates to find, defaults to 25')
    p.add_argument('-t', '--types', nargs='+', default=['Q35120'], help='must be one of these types, defaults to Q35120 (entity)')
    p.add_argument('-b', '--badtypes', nargs='+', default=[], help='mustnot  be one of these types, defaults to none')
    p.add_argument('-ok', '--oktypes', nargs='+', default=[], help='use of one of these types if not enough with target types, defaults to none')        
    p.add_argument('-o', '--out', nargs='?', type=ap.FileType('wb'), default=sys.stdout, help='file for output (defaults to stdout)')
    p.add_argument('--dbpedia', dest='dbpedia', action='store_true', help='get DBpdia abstract and types (default)')
    p.add_argument('--no-dbpedia', dest='dbpedia', action='store_false', help='do not get DBpdia information')
    p.set_defaults(dbpedia=False)
    args = p.parse_args()
    #args.types = [t for t in args.types.split(',')]
    return args


# for performance tracking, these will be incremented for each query
wd_queries = 0
dbp_queries = 0


# sparql endpoint
default_wd_endpoint = "https://query.wikidata.org/bigdata/namespace/wdq/sparql"
default_dbpedia_endpoint = "http://dbpedia.org/sparql"

# user agent for http request (required by wikidata query service) change name as appropriate
USER_AGENT = "SearchBot/2.0 (Tim Finin)"

# search wikidata given a string for entities, filter by requiring a
# type on the target or ok list and no types on the bad list

def wd_search(string, langs=['en'], target_types=[], ok_types=[], bad_types=[], limit=10, top=1, dbpedia=True):
    """ generic search """
    hits = wd_string_search(string, target_types=target_types, ok_types=ok_types, bad_types=bad_types, limit=limit, top=top)
    return [complete_item(hit, langs, dbpedia) for hit in hits]

# version for HLTCOE scale 2021

def wd_scale_search(string, langs=['en'], target_types=['Q35120'], ok_types=[], bad_types=[], limit=20, top=1, dbpedia=True):
    langs = ['en', 'ru', 'zh', 'fa']
    #ok_types += entity_types.scale_types
    bad_types += ['Q17537576'] # + creative work
    
    hits = wd_string_search(string, target_types=target_types, ok_types=ok_types, bad_types=bad_types, limit=limit, top=top)
    #print('hits:', hits)
    
    return [complete_item(hit, langs, dbpedia) for hit in hits]

    
def wd_string_search(string, target_types=[], ok_types=[], bad_types=[], limit=20, top=1):
    
    """ search for up to limit items whose text matches string that
    returns a list ranked by several factors. We want to return the top
    number of them whose types have a target, preferred, or acceptable type and
    do not also have a bad type.  Ones that have a target type will be ranked highest,
    followed by those with a preferred type, followed by ones with only an
    acceptable type. Within each category items are ranked by their intial order,
    which reflects a matching strategy. """
 
    target_types = entity_types.wd_types(target_types)
    ok_types = entity_types.wd_types(ok_types)
    bad_types = entity_types.wd_types(bad_types)

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
        id = item['title']
        targ_types, ok_types = get_types(id, target_types, ok_types, bad_types)
        item['types'] = [t[0] + ':' + t[1] for t in list(targ_types | ok_types)]
        if targ_types:
            target_hits.append(item)
        elif ok_types:
            ok_hits.append(item)
        # stop checking candidates if we have enough hits
        if top and len(target_hits) >= top:
            break

    # return target hits and enough ok hits needed to get to top or as close as possible
    hits = (target_hits + ok_hits)
    if not hits:
        return []
    elif len(hits) > top:
        hits = hits[:top]

    return [{'id':hit['title'], 'types':hit['types'], 'search_string':string} for hit in hits]

def complete_item(item, langs, dbpedia):
    """ item is a dict with an id property that's a wikidata id. Add
    more useful information in a set of languages and, id dbpedia is
    true, from DBpedia. Returns the dict. """

    #print('completing:', item, langs, dbpedia)
    id = item['id']
    item['wd_uri'] = f"https://www.wikidata.org/wiki/{id}"
    item['is_instance'], item['is_type'] = get_isinstance_istype(id)
    item['immediate_types'] = get_immediate_types_labels(id)
    item['wikipedia'] = wp_name = get_en_wikipedia_name(id)
    for lang in langs:
        item[lang] = d = dict()
        ladw = get_ladw(id, lang)
        if any(ladw):
            d['label'], d['aliases'], d['description'], d['wikiname'] = ladw
    if dbpedia:
        item['DBpedia_types'] = get_dbpedia_types(id, wp_name)
        for lang in langs:
            abstract = get_abstract(id, lang, wp_name)
            if abstract:
                item[lang]['abstract'] = abstract
    return item

# SPARQL query to get a wikidata item's type IDs and en labels of type
q_types_labels_query = """
select ?type ?typeLabel where {{
   wd:{QID} wdt:P31/wdt:P279*|wdt:P279* ?type .
   SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}}} """

def wikidata_search(string, limit=20):
    # search wikidata for items containing string in their name, alias or description
    # I think the service is limited to 50 results
    limit = min(limit, 50)    
    api_url = "https://www.wikidata.org/w/api.php"
    params = {'action':'query', 'list':'search', 'srsearch':string, 'srlimit':limit, 'format':'json'}
    result = requests.Session().get(url=api_url, params=params).json()
    return [item for item in result['query']['search']]

# SPARQL query to get a wikidata item's type IDs and en labels of type
q_types_labels_query = """
select distinct ?type ?typeLabel where {{
   wd:{QID} wdt:P31/wdt:P279*|wdt:P279* ?type .
   SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}}} """

def get_types(qid, target_types, ok_types, bad_types, endpoint=default_wd_endpoint):
    """
    Given a wikidata id (e.g., Q7803487) returns a tuple with its types in target_types, ok_types.
    returns immediaely with ([],[], []) if a type in bad_types. We assume that target_types, preferred_types, acceptable_types,
    and bad_types are disjoint.  Each type is represented as a tuple (id, name), e.g., ('Q5', 'human').  If target_types and
    preferred_types are both an empty list or set, all types not in bad_types are considered preferred.
    """
    # retrieve types for wd id
    #print("getting types:", target_types, ok_types, bad_types)
    #alltypes = not(target_types or preferred_types) or target_types == ['']
    query = q_types_labels_query.format(QID=qid)
    results = query_wd(query, endpoint=endpoint)
    ttypes = set()
    oktypes = set()
    for result in results["results"]["bindings"]:
        id_label = (wd_entity_id(result['type']['value']), result['typeLabel']['value'])
        id = id_label[0]
        if id in bad_types:
            #print(f"{qid} bailinging bad type:{id_label}")
            return (set(), set())        
        elif id in target_types:
            ttypes.add(id_label)
        elif id in ok_types:
            oktypes.add(id_label)
    return (ttypes, oktypes)

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
    
def get_immediate_types_labels(id):
    """ Returns a set of the id's immediate types """
    q = f'select ?class ?classLabel where {{wd:{id} wdt:P31 ?class. SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en".}}}}'
    result =  query_wd(q)
    class_labels = set()
    for x in result['results']['bindings']:
        class_labels.add(x['class']['value'].split('/')[-1] + ':' +  x['classLabel']['value'])
    return list(class_labels)

def get_immediate_supertype_labels(id):
    """ id should be a class. Returns a set of the id's immediate supertypes """
    q = f'select ?class ?classLabel where {{wd:{id} wdt:P279 ?class. SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en".}}}}'
    result =  query_wd(q)
    class_labels = set()
    for x in result['results']['bindings']:
        class_labels.add((x['class']['value'].split('/')[-1], x['classLabel']['value']))
    return list(class_labels)


def get_en_wikipedia_name(qid):
    """ Given a wikidata QID, get its en Wikipedia name if it has one, else '' """
    query = f'SELECT ?name WHERE {{?art schema:about wd:{qid}; schema:inLanguage "en"; schema:name ?name; schema:isPartOf <https://en.wikipedia.org/>.}} LIMIT 1'
    results = query_wd(query)
    if results["results"]["bindings"]:
        return results["results"]["bindings"][0]['name']['value'].replace(' ', '_')
    else:
        return ''

def get_abstract(qid, lang='en', name=''):
    """ Get en DBpedia abstract from wikidata qid in a given language, returning '' if none """
    if not name: name = get_en_wikipedia_name(qid)
    # exit with '' if no name<
    if not name: return ''
    query = f'select distinct ?text where {{dbr:{encode_string(name)} dbo:abstract ?text. FILTER(lang(?text) = "{lang}")}}'
    results = query_dbpedia(query)
    # exit with '' if no abstract
    if not results["results"]["bindings"]: return ''
    # there should be only one abstract, return the string
    return results["results"]["bindings"][0]['text']['value']

def get_dbpedia_types(qid, name=''):
    """ returns a list of dbpedia types given qid, a wikidata id """
    if not name: name = get_en_wikipedia_name(qid)
    # exit with [] if no en wikipedia name
    if not name: return [] 
    query = f"select distinct ?t where {{dbr:{encode_string(name)} rdf:type/rdfs:subClassOf* ?t FILTER strstarts(str(?t), str(dbo:))}}"
    results = query_dbpedia(query)
    bindings = results["results"]["bindings"]
    return [remove_prefix(binding['t']['value'], "http://dbpedia.org/ontology/" ) for binding in bindings]    

def remove_prefix(text, prefix):
    return text[len(prefix):] if text.startswith(prefix) else text
    
def get_isinstance_istype(id):
    """ Returns a tuple of two Booleans idicating if id is an instance and is a type """
    q = f"""select distinct ?instance ?type where {{
          BIND (exists {{wd:{id} wdt:P31 []}} AS ?instance) 
          BIND (exists {{wd:{id} wdt:P729 []}} AS ?type) }}"""
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

def summary1(hit):
    if hit:
        return (hit['id'], hit['en']['label'], hit['en']['description'], "https://wikidata.org/wiki/"+hit['id'])
    else:
        return ('', '', '', '')

def summary(hits):
    if type(hits) == list:
        return [summary1(h) for h in hits]
    else:
        return summary1(hits)
    

def main(args):
    result = wd_search(args.string, langs=args.lang, limit=args.limit, target_types=args.types, ok_types=args.oktypes, bad_types=args.badtypes, top=args.top, dbpedia=args.dbpedia)
    print(f"Queries to wikidata:{wd_queries}, DBpedia:{dbp_queries}")
    with args.out as out:
        out.write(hits_string(result))
        out.write('\n')

if __name__ == '__main__':
    args = get_args()
    main(args)


