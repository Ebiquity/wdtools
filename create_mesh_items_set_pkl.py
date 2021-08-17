"""

Creates the file mesh_items.pkl that when loaded creates a set of the
wikidata qids that are linked to a mesh term (a Medical Subject
Headings controlled vocabulary term from UMLS).

uses the file mesh_items.txt that was obtained via wikidata using this sparql query

https://query.wikidata.org/sparql?query=select%20distinct%20%3Fqid%20%7B%0A%20%20%3Fqid%20wdt%3AP486%20%3Fany%7D

Load the pickle file like this:
    with open('mesh_items.pkl', 'rb') as infile: 
        mesh_items = pickle.load(infile)

and check to see if a QID is in the set like: 'Q42' in mesh_trms

"""

import pickle

mesh_items = set()

for line in open('mesh_items.txt'):
    mesh_items.add(line.strip())

with open('mesh_items.pkl', 'wb') as outfile:
    pickle.dump(mesh_items, outfile, protocol=pickle.HIGHEST_PROTOCOL)

'DONE'
