## Wikidata entiy linking tools

Tools to link entities and concepts in text to Wikidata items and to
extract useful information from the Wikidata knowledge graph


Entities play an important role in text and are often used to describe what the text is about. One approach we evaluated was to find entity mentions in a report or document, link these to corresponding entities in the Wikidata knowledge graph, and use their information to improve the search.

### Document entities

We use SpaCy to process text in a report or document and identify the named entity mentions along with their type.  The standard SpaCy pipelines for most common languages come with a named entity recognition module that has been trained to identify the relatively limited set of Ontonotes types \cite{hovy2006ontonotes}. While it works reasonably well, it does miss some named entities and often assign the wrong type to entities that are found.

SpaCy's predefined pipelines also do not do coreference, i.e., identifying a set of entity mentions, nominal  mentions and pronouns that refer to the same entity. This can be important for many subsequent tasks, such as noting how often an entity was mentioned in a document.  We experimented with the addition of a simple coference tool that recognized name shortening (e.g., "Joe Biden" and "Biden") and abbreviations (e.g., "World Health Organization" and "WHO") for coreference.  

The Ontonotes named entities refer to a instance of type, such as an individual person or organization, a specific location, or a nationality. We also experimented with identifying potential mentions of concepts that might be linkable, such as "letter bomb", "lava flow" or "potentially hazardous asteroid". Our strategy was simple: look for a nominal compound possible preceded by an adjective.

### Wikidata entities

Wikidata is a collaboratively edited multilingual knowledge graph that is intended to provide common data for Wikipedia sites and other applications. It currently has about one billion facts on about 100 million items.  It has a web interface to support exploration and editing by people, a set of APIs to access its information programmatically, and a SPARQL endpoint for querying RDF model of the knowledge graph.  Wikidata's ontology has very fine-grained type system with more than two-million types and a much smaller set of properties, currently about NNNNN in number.

Wikidata is inherently multilingual and draws on data from more Wikipedia sites in nearly 300 different languages.  It gives each item a identifier beginning with the letter Q like Q64780099 (the Human Language Technology Center of Excellence), and each property an id beginning with the letter P, for example P31, which is the property "instance of" that links an item with one of its immediate types and P279 that links a type to one of its immediate super--types.


### Entity linking

...
