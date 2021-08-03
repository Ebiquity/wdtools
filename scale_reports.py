"""

Process a scale jonl file of topics to add information on entities and concepts found in various text elements (title, description and report.

tim finin, finin@umbc.edu
"""

#MODEL = "md"
MODEL = "lg"
#MODEL = "trf"
#MODEL = "stanza"


from collections import defaultdict
import time
import sys
import json
import argparse as ap
import datetime
import emoji

if MODEL == "stanza":
  print("Using spacy stanza")
  import stanza
  import spacy_stanza
  nlp = spacy_stanza.load_pipeline("en")  
elif MODEL == "trf":
    print("Using spacy trf")    
    import spacy
    nlp = spacy.load("en_core_web_trf")
    import tensor2attr
    nlp.add_pipe('tensor2attr')
elif MODEL == "md":
    print("Using spacy md")  
    import spacy
    nlp = spacy.load("en_core_web_md")
else:
    print("Using spacy lg")  
    import spacy
    nlp = spacy.load("en_core_web_lg")

from spacy.matcher import Matcher
from abbreviation import AbbreviationDetector

import spacy_plus as sp   # addiional spacy related functions

import wd_search as wds   # code for searching the public wikidata server
# import gkg_search as gkg  # code for search the google knowledge graph


# Add the abbreviation pipe to the spacy pipeline.
nlp.add_pipe("abbreviation_detector")

# outpput to record when the data was generated
TIMESTAMP = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# maximum number of report topics to use, use a low number (e.g., 3) as another way for debugging
MAX_FILES = 300

# used for a link when an entity or concept cannot be linked
NOLINK = {'id':'Q0', 'qid':'Q0', 'labels':{'en':'ZZZZZ'}, 'aliases':{}, 'descriptions':{}, 'score' : 0 } # value to use for a null link

# number of example sentences to show for an entity of concept
MAX_SENTENCES_TO_SHOW = 1

# number of characters to show in slice of sentence containing an entity or concept
MAX_SENTENCE_LENGTH = 100 

# SpaCy entity types to ignore
IGNORE_TYPES = ['QUANTITY','DATE','ORDINAL','CARDINAL', 'MONEY', 'PERCENT', 'TIME', 'NORP']

# which systems should we use for linking entities
use_wd = True
use_google = False

# what links should we seek
link_named_entities = True
link_nominal_concepts = True

# initialize link_string variables that record document-specific coref & abbreviation relations
sp.reset_link_string() 

# define a matcher to look for sequences of two or more nouns
if link_nominal_concepts:
    nc_matcher = Matcher(vocab=nlp.vocab)
    #nominal_compound = [{'POS': 'NOUN', 'OP': '+'}, {'POS': 'NOUN'}]
    nominal_compound = [{'POS':'ADJ', 'OP':'?'},{'POS':'NOUN', 'OP':'+'}, {'POS':'NOUN'}]    
    nc_matcher.add("possible concepts", patterns=[nominal_compound])

# what parts of the topic should we process
process_reports = True
process_titles = True
process_descriptions = True

topics = {}                         # dict from topic with ids as keys
    
gkglink = {}                        # dict from ents to links from Google Knowledge Graph
em_count = defaultdict(int)         # dict from ents to number of mentions in all topics
em_count_topic = {}                 # dict from ents to number of mentions in a document
topic2em_count = {}                 # dict from topic to em to count of that mention in the topic

topic2em2sents = {}                 # dict from topic part to mention to list of sentences mention was in
topic2elid_count = {}               # dict from topicid entity link counts
el_count = defaultdict(int)         # dict from entity links to number of entity links in all topics
#el_count_topic = {}                # dict from entity links to number of mentions in a document
el2topics = defaultdict(set)        # dict from links to a set of topics in which they are mentioned
topic2em2links = {}                 # dict mapping a topic part's mentions to a list of possible links
topic2emtext2links = {}             # dict mapping a topic part's mentions to a list of possible links
topic2em2link = {}                  # dict mapping a topic part's mentions to best single link
#topic2emtext2link = {}             # dict mapping a topic part's mentions to a list of possible links

topic2links = defaultdict(dict)     # dict from topic parts to a dict of links
topic2linkid2sents = {}             # dict from topic parts to their links' sentences
linkid2link = {}                    # dict from link id (i.e., Qnnnnn) to the link

nc_count = defaultdict(int)
nc2sents = defaultdict(list)
topic2nc_count = {} 
ncl_in_topic = defaultdict(set)
nc2link = {}
                
start_time = time.time()

TOPIC_PARTS = ['title', 'description', 'report']

def process_topic_file(infile, outfile, summary_file, topic_ids_todo):
    global start_time, topic2linkid2sents
    
    start_time = time.time()

    for linecount, line in enumerate(open(infile)):
        if linecount > MAX_FILES: break
        data = json.loads(line)
        topic_id = data['topic_id']
        if topic_ids_todo and topic_id not in topic_ids_todo: continue

        topics[topic_id] = {'topic_id':topic_id}
        topics[topic_id]['title'] = data['topic_title']
        topics[topic_id]['description'] = data['topic_description']
        topics[topic_id]['report'] = truncate(data['report_text'], 100)
        topics[topic_id]['parts'] = [(topic_id, 'report'), (topic_id, 'description'), (topic_id, 'title')]

        topic2linkid2sents = {}
        topic2linkid2sents[topic_id] = {}
    
        # initialize link_string variables that record document-specific coref & abbreviation relations
        sp.reset_link_string() 

        for part in topics[topic_id]['parts']:
            if part == (topic_id, 'title'):
                text = data['topic_title']
            elif part == (topic_id, 'description'):
                text = data['topic_description']
            else:
                text = data['report_text']

            print('Processing part', part, truncate(text, 100).replace('\n', ' '))
            topic2em_count[part] = defaultdict(int)    # record frequency of entity mention in topic
            topic2nc_count[part] = defaultdict(int)    # record frequency of nominal coumpund in topic
            #el_count_topic[part] = defaultdict(int)   # record frequency of entity link in topic
            topic2elid_count[part] = defaultdict(int)  # record frequency of entity link in topic
            topic2em2links[part] = defaultdict(list)      # maps em (string,type) to list of possible links in this topic part
            topic2emtext2links[part] = defaultdict(list)      # maps emtext string to list of possible links in this topic part


            topic2em2link[part] = {}                     # maps em, i.e. (string,type), to best link
#            topic2emtext2link[part] = {}                 # maps em text, i.e. string,  to best link            
            topic2em2sents[part] = defaultdict(list)   # list of sentences
            topic2linkid2sents[part] = defaultdict(set)
            
            # process a part of the topic
            doc = nlp(text)
            sp.find_link_strings(doc)

            if link_named_entities:
                 process_named_entity_mentions(doc, part)

            if link_nominal_concepts:        
                 process_nominal_concepts(doc, part)

            # update the counts in the links for this part (safe to do since we made shallow copies)
            #for link in topic2links[part]:
            #    link['counts'] = topic2elid_count[part][link['id']]
                 
    if outfile:
        write_outfile(infile, outfile, topic_ids_todo) 
    if summary_file: 
        write_summary_file(summary_file)
    print('fin')
    

def process_named_entity_mentions(doc, topic_id):
    """ topic_id is a tuple like ('10', 'report') """

    global topic2linkid2sents

    for ent_mention in doc.ents:
        em_text = ent_mention.text
        em_type = ent_mention.label_
        em_sentence = ent_mention.sent
        if em_type in IGNORE_TYPES:
            continue
        if sp.alldigits(em_text):   # dont link mention that is all digits (possibly with spaces)
            continue
        
        em_text = sp.trim(em_text)   # experimental trimming (e.g., removes initial 'The')
        link_text = sp.link_string[em_text] if em_text in sp.link_string else em_text
        em = (link_text, em_type)

        # if link_text != em_text: print(f"using {link_text} for linking {em_text}")

        em_count[em] += 1   # increment mentionfrequency  seen in any topic
        topic2em2sents[topic_id][em].append(ent_mention.sent)  #sentences mention is in
        topic2em_count[topic_id][em] += 1   # count of this ent in topic doc

        # find best link for this mention given its sentence
        link = wds.link(link_text, target_types=[em_type], category='all', top=3, context=em_sentence)
        if not link:
            topic2em2link[em] = NOLINK
            continue
        #print(f"linked '{link_text}' of type {em_type} to {link['id']}")        
        link['source'] = "entity"
        topic2em2links[topic_id][em].append(link)
        topic2emtext2links[topic_id][link_text].append(link)        
        topic2elid_count[topic_id][link['id']] += 1  # increment count of link in this topic        

    # we assume that each unique mention in a doc, e.g. (Trump,PER),
    # should link to just one WD item so choose the best one.

    final_links = {}   #dict from qids to a link dict
    for emtext, links in topic2emtext2links[topic_id].items():
        #print(f"{emtext} : {[l['id'] for l in links]}")
        analyze_links(em,links)  # only for human output
        scores = [ x['score'] for x in links]
        ranks =  [ x['rank'] for x in links]
        best_link = min(links, key = lambda link: link['rank'])
        best_link['counts'] = len(links)
        best_score = best_link['score']
        # for campatibility with Elliot's system
        best_link['scores'] = {'ts_prob':scores, 'score':scores, 'rank':ranks}
        qid = best_link['qid']
        if qid not in final_links:
            final_links[qid] = best_link
            #print(f"initial final_links: {final_links}")
        else:
            #merge info on counts and scores
            #print(f"afdding to final_links: {best_link}")            
            final_links[qid]['counts'] += best_link['counts']
            final_links[qid]['scores']['ts_prob'] += best_link['scores']['ts_prob']
            final_links[qid]['scores']['score'] += best_link['scores']['score']
            final_links[qid]['scores']['rank'] += best_link['scores']['rank']            

        #topic2emtext2link[topic_id][emtext] = best_link
        topic2links[topic_id] = final_links

    # this data is only for the human-readable output
    for em, links in topic2em2links[topic_id].items():
        best_link = min(links, key = lambda link: link['rank'])
        topic2em2link[topic_id][em] = best_link        

# analyze how often we get the same or different links for a mention in a document 
link_analysis = defaultdict(int)
confused_links = []
def analyze_links(em, links):
    global link_analysis
    if len(links) == 1:
        link_analysis[0] += 1
        return
    linkids = set()
    for link in links:
        linkids.add(link['id'])
    link_analysis[len(linkids)] += 1
    if len(linkids) > 1:
        confused = [(l['id'], l['labels']['en'], l['score']) for l in links]
        confused_links.append((em, confused))
        
def avg(l):
    return sum(l)/len(l)

def process_nominal_concepts(doc, topic_id):
    """ process all of the nominal cocepts from doc in this topic"""
    global nc_matcher, ncl2el

    links= [ ]   # phrase links found in this topic part

    nominals = nc_matcher(doc, as_spans=True)

    #print('Nominals:', nominals)
    for nc in nominals:
        if bad_nc(nc):
            continue
        nctext = sp.get_nc_text(nc)               # replaces last noun with its lemma
        ncsent = nc.sent.text.replace('\n','')    # sentence the nc is in
        nc_count[nctext] += 1                     # increment number times the mention seen in any topic
        nc2sents[nctext].append(ncsent)
        topic2nc_count[topic_id][nctext] += 1     # count of this ent in topic doc
                    
        if nc_count[nctext] == 1:                 # first time seen in any document, find link
            link = wds.link(nctext, category='strictconcept', top=3, context=ncsent) or NOLINK
            nc2link[nctext] = link
            if link == NOLINK:
                continue
            link['source'] = "phrase"
            ncl_in_topic[topic_id].add(link['id'])
            links.append(link)
            #print(link)
        else:                    # seen before, use its link
            link = nc2link[nctext]
            if link == NOLINK:
                continue

        link_id = link['id']
        el_count[link_id] += 1                      # increment count of link in any topics
        topic2elid_count[topic_id][link_id] += 1    # increment count in this topic
        el2topics[link_id].add(topic_id)            # add this topic part as one the link appears in

    # add nc links found in topic part
    for link in links:
        qid = link['qid']
        link['counts'] = el_count[link['qid']]
        link['scores'] = {'ts_prob': [link['score']], 'score': [link['score']], 'rank':[link['score']]}
        if qid not in topic2links[topic_id]:
            topic2links[topic_id][qid] = link # xxx
        else:
            #merge info on counts and scores
            l = topic2links[topic_id][qid]
            l['counts'] += link['counts']
            l['scores']['ts_prob'] += link['scores']['ts_prob']
            l['scores']['score'] += link['scores']['score']
            l['scores']['rank'] += link['scores']['rank']            

        
def bad_nc(nc):
    """ SpaCy finds three nc's for letter-bomb: letter-, -bomb, and letter-bomb """
    for token in nc.text.split(' '):
        if token[0] == '-' or token[-1] == '-':
            return True
    return False

def write_outfile(infile, outfile, topic_ids_todo=[]):
    """ update the input json file to include the entities found in the title, description and report """
    global TIMESTAMP
    
    with open(outfile, 'w') as out:                
    #with open(outfile, 'w', encoding='unicode-escape') as out:                

        for linecount, line in enumerate(open(infile)):
            if linecount > MAX_FILES: break
            in_data = json.loads(line)
            topic_id = in_data['topic_id']
            if topic_ids_todo and topic_id not in topic_ids_todo:
                out.write(line)
            else:  # add linking data to this line's json object
                in_data['resources'] = {'entity_linking' : {
                    'title_text': {'entities': topic2links[(topic_id, 'title')]},
                    'description_text': {'entities': topic2links[(topic_id, 'description')]},
                    'report_text': {'entities': topic2links[(topic_id, 'report')]},
                    'time_stamp' : TIMESTAMP,
                    'eval' : '',
                    'inbox' : ''}}
                # write out the line
                #out.write(json.dumps(in_data, ensure_ascii=False))
                out.write(json.dumps(in_data))
                out.write('\n')
            
def truncate(string, max):
    return string if len(string) <= max else string[:max] + "..."

def text_has_emoji(text):
    for character in text:
        if character in emoji.UNICODE_EMOJI:
            return True
    return False

def link_summary(link):
    # returns (id, label, description) for en
    label = link['labels']['en'] if 'en' in link['labels'] else ''
    desc = ''
    if 'en' in link['descriptions']:
        desc = truncate(link['descriptions']['en'], 80)
    return (link['id'], label, desc )


def write_summary_file(outfile):
    """ The summary file as information that can help assess what the processing found """

    global topics

    elapsed = time.time() - start_time
    total_mentions = sum(em_count.values())
    total_nominal_compounds = sum(nc_count.values())
    total_linked_entities = len(el_count)
    #total_linked_nominal_compounds = len(ncl_count)    #fixme

    with open(outfile, 'w') as out:
        out.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        out.write(f"\nSpaCy and linking took {elapsed:.1f} seconds to process {total_mentions} mentions and link them to {total_linked_entities} wikidata entities\n")

        # only useful if we're using context for linking entities
        #out.write(f"\nLink analysis: {link_analysis} \n")
        #out.write(f"\n  confused links: {confused_links}")
        
        for topic in topics.keys():
            for part in [(topic, 'title'), (topic, 'description'), (topic, 'report')]:

                out.write(f"\n\n-------------------- {part[0]} {part[1]} --------------------\n")

                out.write(f"text: {topics[topic][part[1]]}\n")

                entity_mentions = sorted(topic2em_count[part].keys())
                total_mentions_in_report = sum(topic2em_count[part].values())
                out.write(f"\nENTITY MENTIONS: {total_mentions_in_report} ({len(entity_mentions)} unique) linked to {len(topic2elid_count[part].keys())} Wikidata entities\n")
                for em in entity_mentions:
                    count = topic2em_count[part][em]
                    link = link_summary(topic2em2link[part][em]) if em in topic2em2link[part] else NOLINK
                    out.write(f"{count} {em}; LINK:{link}\n")
                    for sent in topic2em2sents[part][em][0:MAX_SENTENCES_TO_SHOW]:
                        stext = sent.text.replace('\n',' ')
                        s = sp.entity_in_text(em[0], stext, MAX_SENTENCE_LENGTH)
                        out.write(f"  {s}\n")  # print MAX_SENTENCE_LENGTH characters
    
                nominal_compounds = sorted(topic2nc_count[part].keys())    
                total_ncs_in_report = sum(topic2nc_count[part].values())
                out.write(f"\nCONCEPT MENTIONS: {total_ncs_in_report} ({len(nominal_compounds)} unique) linked to {len(ncl_in_topic[part])} Wikidata concepts\n")
                for nc in nominal_compounds:
                    count = topic2nc_count[part][nc]
                    if nc2link[nc] == NOLINK: # don't show unlinked nominal concepts
                        continue
                    out.write(f"{count} {nc}; LINK:{link_summary(nc2link[nc])}\n")
                    for sent in nc2sents[nc][:MAX_SENTENCES_TO_SHOW]:
                        stext = sent.replace('\n',' ')
                        s = sp.entity_in_text(nc, stext, MAX_SENTENCE_LENGTH)
                        out.write(f"  {s}\n")  # print MAX_SENTENCE_LENGTH characters

                # show linkids and frequency in topic part
                links = sorted(topic2elid_count[part].items(), key=lambda t: t[1], reverse=True)
                out.write(f"\n{len(links)} LINKS: {links}")
                    
def write_topic_stats(out):
    out.write(f"\n\n-------------------- summary over all topics --------------------\n")
    out.write("\nTop ten mentions in all topics\n")
    for mention, count in sorted(em_count.items(), key=lambda x: x[1], reverse=True)[:10]:
        out.write(f"{count}\t{mention}\n")
    out.write("\nTen linked entities/concepts appearing the most topics\n")
    for link, topics in sorted(el2topics.items(), key=lambda link_topicSet: len(link_topicSet[1]), reverse=True)[:10]:
        out.write(f"{len(topics)}\t{link}\n")


def get_args():
    p = ap.ArgumentParser()
    p.add_argument('topic_infile', help='path to the input jsonl file of topics')
    p.add_argument('topic_outfile', help='path to the output jsonl file of topics')
    p.add_argument('summary_outfile', nargs='?', default='', help='file for human readable output on run')
    p.add_argument('-t', '--topics', nargs='+', default=[], help='topic numbers to process, e.g., for a debugging run')
    args = p.parse_args()
    return args

def main(args):
    process_topic_file(args.topic_infile, args.topic_outfile, args.summary_outfile, args.topics)

if __name__ == '__main__':
    main(get_args())
