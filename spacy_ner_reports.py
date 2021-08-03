import spacy
import en_core_web_lg  # medium en pipeline
import wd_search as wds
import gkg_search as gkg
import spacy_plus as sp

from collections import defaultdict
import time
import sys
import json

# maximum number of report topics to use
MAX_FILES = 300

# which systaems shuld we use for linking entities
use_wd = True
use_google = True

nlp = spacy.load("en_core_web_trf")
#nlp = spacy.load("en_core_web_md")

infile = sys.argv[1]      # first arg is infile
outfile = sys.argv[2]     # second arg is outfile
if len(sys.argv) > 3:     # any remaining args are report numbers we're interedted in
    topic_ids_todo = sys.argv[3:]
else:
    # do all topic_ids
    topic_ids_todo = []       

print(f"extracting topic reports from {infile} writing to {outfile}")

topics = {}                         # fict from topic with ids as keysP
    
#wdlink = {}                         # dict from ents to links from Wikidata
gkglink = {}                        # dict from ents to links from Google Knowledge Graph
#em_in_topic = defaultdict(set)      # dict from topicid to a set of ents
em_count = defaultdict(int)         # dict from ents to number of mentions in all topics
em_count_topic = {}                 # dict from ents to number of mentions in a document
topic2em_count = {}                 # dict from topic to em to count of that mention in the topic

em2el = {}                          # dict from mentions to link
em2sentences = defaultdict(list)    # dict from mention to list of sentences it was in
el_in_topic = defaultdict(set)      # dict from topicid to a set of entity links
el_count = defaultdict(int)         # dict from entity links to number of entity links in all topics
el_count_topic = {}                 # dict from entity links to number of mentions in a document
el2topics = defaultdict(set)        # dict from links to a set of topics in which they are mentioned

canonical = {}                      # dict from a ent to its canonical coref

line_count = 0

NOLINK = ('Q0', "ZZZZZ")  # value to use for a null link

start_time = time.time()
for line in open(infile):
    line_count += 1
    if line_count > MAX_FILES:
        break

    data = json.loads(line)
    topic_id = data['topic_id']
    if topic_ids_todo and topic_id not in topic_ids_todo:
        continue
    topics[topic_id] = {'topic_id':topic_id}
    topics[topic_id]['title'] = data['topic_title']
    topics[topic_id]['description'] = data['topic_description']

    print('processing', topic_id)
    topic2em_count[topic_id] = defaultdict(int)   # record frequency of entity mention in topic
    el_count_topic[topic_id] = defaultdict(int)   # record frequency of entity link in topic
    report_text = data['report_text']

    doc = nlp(report_text)
    sp.find_link_strings(doc)

    for ent_mention in doc.ents:
        em_text = ent_mention.text
        em_type = ent_mention.label_
        if em_type in ['QUANTITY','DATE','ORDINAL','CARDINAL', 'MONEY', 'PERCENT', 'TIME']:     # we dont link these types of entities
            continue
        if sp.alldigits(em_text):    # we dont link these types of entities
            continue
        em_text = sp.trim(em_text)           # experimental trimming
        em = (em_text, em_type)
        em_count[em] += 1                    # increment number times the entity mention seen in any topic
        em2sentences[em].append(ent_mention.sent.text.replace('\n',''))
        topic2em_count[topic_id][em] += 1    # count of this ent in topic doc
                    
        if em_count[em] == 1:  # first time seen in any document, find link
            link_text = sp.link_string[ent_mention] or em_text
            if use_wd:  # get link from wikidata
                wd_result = wds.link(link_text, target_types=[em_type], category='all')
                if wd_result:
                    #link = (wd_result['id'], wd_result['en']['label']) # if wd_result else NOLINK     # el is the linked wikidata entity
                    link = wds.summary(wd_result) # if wd_result else NOLINK
                    el_in_topic[topic_id].add(link)
                    em2el[em] = link
                elif use_google:                        # backup if no link in wikidata, try google
                    gkg_result = gkg.link(link_text, target_types=[em_type])
                    if gkg_result:
                        link = gkg.summary(gkg_result)
                        #wdlink[em] = link
                        el_in_topic[topic_id].add(link)
                        em2el[em] = link
                    else:
                        # neither wikidata nor google had a link :(
                        #wdlink[em] = NOLINK
                        el_in_topic[topic_id].add(NOLINK)
                        em2el[em] = NOLINK
        else:  #we've seen a mention before with this text and type, so use its link
            link = em2el[em]
            el_in_topic[topic_id].add(link)

        el2topics[link].add(topic_id)
        el_count_topic[topic_id][link] += 1    # increment count of link in topic
        el_count[link] += 1                    # increment count of link in any topicbsc
        

elapsed = time.time() - start_time
total_mentions = sum(em_count.values())
total_linked_entities = len(el_count)


with open(outfile, 'w') as out:

    out.write(f"SpaCy and linking took {elapsed:.1f} seconds to process {total_mentions} mentions and link them to {total_linked_entities} wikidata entities\n")


    for topic in topics.keys():
        out.write(f"\n\n-------------------- {topic_id} --------------------\n")

        out.write(f"Title: {topics[topic]['title']}\n")
        out.write(f"Description: {topics[topic]['description']}\n")
        
        entity_mentions = sorted(topic2em_count[topic].keys())    
        total_mentions_in_report = sum(topic2em_count[topic].values())
        out.write(f"\nReport has {total_mentions_in_report} entity mentions ({len(entity_mentions)} unique) linked to {len(el_in_topic[topic])} Wikidata entities \n")
        
        for em in entity_mentions:
            count = topic2em_count[topic][em]
            out.write(f"{count} {em}; LINK:{em2el[em]}\n")
            for sent in em2sentences[em]:
                s = sp.entity_in_text(em[0], sent, 120)
                out.write(f"  {s}\n")  # print first 120 characters

    out.write(f"\n\n-------------------- summary --------------------\n")

    out.write("\nTop ten mentions in collection\n")
    for mention, count in sorted(em_count.items(), key=lambda x: x[1], reverse=True)[:10]:
        out.write(f"{count}\t{mention}\n")

    out.write("\nTen links appearing the most topics\n")
    for link, topics in sorted(el2topics.items(), key=lambda link_topicSet: len(link_topicSet[1]), reverse=True)[:10]:
        out.write(f"{len(topics)}\t{link}\n")            

