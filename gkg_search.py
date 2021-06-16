""" Example of Python client calling Knowledge Graph Search API """

import entity_types as et  # mapping of entity type names  between different systems (e.g., ontonotes, wikidata, schema.org, ...

import sys, json, argparse
import argparse

from urllib.request import urlopen
from urllib.parse import urlencode

SERVICE_URL = 'https://kgsearch.googleapis.com/v1/entities:search'  # for google knowledge graph queries

USAGE = """USAGE: python gkg_search .py 'Springfield IL' --limit 10 --top 2 --types 'Organization Place' --languages = 'ru' """

# A profile of defauts for hltcoe scale 2021
DFS = {
 'langs' : ['en', 'ru', 'zh', 'fa'],
 'target_types' : ['Thing'], 
 'ok_types' : [],
 'bad_types' : [],
 'limit' : 10,
 'top' : 1,
}


# read api key from file
default_api_key = open('.api_key').read().rstrip()  # free, but required.  Current limits are 100k queries per day per key

default_types = ['Thing']      # defaults to 'Thing'
default_languages = []  # service defaults to en
default_limit = 10      # number of candiates to consider
default_top = 2         # number of top-ranked canaidates to return

# These are types I've seen.  There may be a few more.  They are case-sensitive!

typestrings = """Action|AdministrativeArea|Animal|BodyOfWater|Book|Brand|CollegeOrUniversity|Corporation|Corporation|Country|CreativeWork|EducationalOrganization|Event|Intangible|MedicalEntity|Movie|MovieTheater|MusicAlbum|MusicComposition|Organization|PerformingGroup|Periodical|Person|Place|Product|ProductModelRiverBodyOfWater|Religion|SoftwareApplication|SportsOrganization|SportsTeam|Thing|TVSeries|Vehicle|VideoGame"""

gkg_types = set('|'.split(typestrings))

def gkg_query(query, limit, types, languages, key):
    """ returns a JSON object with data from the google knowledge graph """
    tt = set()
    for t in types:
        for s in et.names2schematypes[t]:
            tt.add(s)
    types = tt

    params = {'query':query, 'limit':limit, 'key':key}
    query_url = SERVICE_URL + '?' +  urlencode(params)
    
    for lang in languages:
        query_url += f"&languages={lang}"
    for t in types:
        query_url += f"&types={t}"        
    #print('query_url:', query_url)
    return json.loads(urlopen(query_url).read())["itemListElement"]


def gkg_search(query, limit=default_limit, top=default_top, target_types=['Thing'], bad_types=[], languages='', key=default_api_key):
    # simplifies the response by returning just a list of hits, removing some properties and
    # using @language for the detailed description language property.  Note that limit controls how many
    # matches google finds.  After finging them it sorts by some ranking mesure.  It's good to have limit>top
    # since the highest-ranking item might not be found first.  Top controls how many are returned by this function.
    # bad_types filter not yet implemented
    
    results = []
    candidates = gkg_query(query, limit, target_types, languages, default_api_key)
    # eliminate bad_types here...
    for element in candidates[:top]:
        result = element['result']
        result['resultscore'] = element['resultScore']
        if 'detailedDescription' in result:
            simplify_detailed_description(result['detailedDescription'])
        results.append(result)
    return results

def simplify_detailed_description(dd):
    "result of ocd"
    if type(dd) == list:
        for item in dd: simplify_detailed_description(item)
    else:
        del dd['license']
        if 'inLanguage' in dd:
            dd['@language'] = dd['inLanguage']
            del dd['inLanguage']

def link(string, target_types=DFS['target_types'], bad_types=DFS['bad_types']):
    """ return the top hit. default type is 'Thing' """
    results = gkg_search(string, target_types=target_types, bad_types=bad_types, limit=10, top=1)
    return results[0] if results else None
            
def summary1(hit):
    if hit:
        if 'detailedDescription' in hit:
            return (hit['@id'], hit['name'], hit['detailedDescription']['articleBody'][:60]+"...")
        else:
            return (hit['@id'], hit['name'])
    else:
        return ''
    #return (hit['id'], hit['en']['label'], hit['en']['description'], "http://wikidata.org/wiki/"+hit['id'])
    #return (hit['id'], hit['en']['label'], hit['en']['description'], hit['types'], "http://wikidata.org/wiki/"+hit['id'])

def summary(hits):
    #print('hits:', hits)
    if type(hits) == list:
        return [summary1(h) for h in hits]
    elif hits:
        return summary1(hits)
    else:
        return 'No match'
            

def get_args():
    # PD is s profile of defaults, typically either DF or DFS
    p = argparse.ArgumentParser(description='query google knowledge graph for entities mating string and other args')
    p.add_argument('query', help='string to search for, e.g. "brad pitt" ')
    p.add_argument('-l', '--languages', nargs='+', default=['en'], help='return string data in these 2-letter language codes, defaults to en' )
    p.add_argument('--top', nargs='?', type=int, default=2, help='number of ranked hits to return, defaults to 2')
    p.add_argument('--limit', nargs='?', type=int, default=20, help='number of initial candidates to find, defaults to 20')
    p.add_argument('-t', '--types', nargs='+', default=['Thing'], help='required types, use ontonotes or schema.org types, degaults to "Thing"')
    p.add_argument('-b', '--bad_types', nargs='+', default=[], help='must not be one of these types, defaults to []')
    #p.add_argument('-o', '--out', nargs='?', type=ap.FileType('wb'), default=sys.stdout, help='file for output (defaults to stdout)')
   # p.set_defaults(PD['dbpedia'])
    return p.parse_args()


def main(args):
    hits = gkg_search(args.query, limit=args.limit, top=args.top, target_types=args.types, bad_types=args.bad_types, languages=args.languages)
    print(json.dumps(hits, indent = 2, separators=(",", ":"), sort_keys=True, ensure_ascii=False))    
    
if __name__ == '__main__':
    main(get_args())
