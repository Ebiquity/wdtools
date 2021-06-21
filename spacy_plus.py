
from collections import defaultdict
import re

def trim(text):
    """ Hack to trim text from some entity mentions """
    orig_text = text
    if text.startswith('The ') or text.startswith('the '):
        text = text[4:]
    if text.endswith('\n'):
        text = text[:-1]
    if text.endswith("'"):
        text = text[:-1]
    elif  text.endswith("'s"):
        text = text[:-2]
    #if text != orig_text: print(f"trimming {orig_text} => {text}")
    return text

def alldigits(text):
    """ Returns True iff the text string is composed of just digits or spaces """
    for char in text:
        if char not in '0123456789 ':
            return False
    return True

# this should be local to a document (i.e., topic part), so reset it as needed
link_string = defaultdict(str)

def find_link_strings(doc):
    """ checks entity mentions of types PERSON and ORG to predict coreference """
    
    global link_string
    link_string = defaultdict(str)

    for e in doc.ents:
        if e.end - e.start > 1 or e.label_ != 'PERSON':
            continue
        etl = (e.text, e.label_)
        if etl in link_string:
            pass
            #print(f"Already linking {etl} to {link_string[etl]}")
        etext = trim(e.text).lower()
        matches = []
        for e2 in doc.ents:
            if e == e2 or e2.label_ != 'PERSON' or e2.end - e2.start == 1 :
                continue
            e2_final_word = e2.text.split(' ')[-1]
            e2text = trim(e2_final_word).lower()
            if etext == e2text:
                matches.append(e2.text)
        if matches and matches.count(matches[0]) == len(matches):
            link_string[etl] = matches[0]
            #print(f"Coref {etl} to {matches[0]}")

    for e in doc.ents:
        # for a one word entity that looks like an abbreviation, look for an examded version
        if e.end - e.start == 1 and e.label_ in ['ORG', 'LAW'] and e.text.isupper() and 1 < len(e.text) < 8:
            #print(f"Checking possible abbreviation {e.text}")
            matches = [ ]
            # match mentions that yield a plausible abbreviation
            for e2 in doc.ents:
                if e != e2 and e2.label_ == e.label_ :
                    e2tokens =  re.split(' |-', e2.text)
                    #e2tokens = e2.text.split(' ')
                    if e2tokens[0] in ["The", "the", "a", "an", "A", "An"]:
                        #print('trimming', e2tokens[0])
                        e2tokens = e2tokens[1:]
                    if len(e2tokens) != len(e.text):
                        continue
                    #print('e2tokens:', e2tokens)
                    abbreviation = abbreviate(e2tokens)
                    #print(f"  Abbreviate {e2.text} as {abbreviation} ")
                    if e.text == abbreviation:
                        matches.append(' '.join(e2tokens))
            # check if all matches are the same string
            #if matches:  print(f"  Matches: {matches}")
            if matches and matches.count(matches[0]) == len(matches):
                #link_string[e] = matches[0]
                etl = (e.text, e.label_)
                link_string[etl] = matches[0]
                #print(f"Coref {etl}  to {matches[0]}")

def abbreviate(tokens):
    """ Generate a possible abbreviation for a list of tokens """
    stopwords = ['in', 'of', 'for', 'on']
    tokens = [t for t in tokens if not t in stopwords]
    return ''.join([t[0] for t in tokens]).upper()

def entity_in_text(etext, sentence, max_length):
    """ puts brackets around etext in sentence and snhows a window of at most max_length around etext """
    etext1 = "[" + etext + "]"
    sentence1 = sentence.replace(etext, etext1, 1)
    estart = sentence1.find(etext1)
    context_length = (max_length - len(etext1))
    start = max(0, estart - int(context_length/2))
    return sentence1[start:start+max_length+1]


def get_nc_text(nc):
    last = nc[-1]
    lemma = last.lemma_
    if lemma != last.text:
        return nc.text.replace(last.text, lemma)
    else:
        return nc.text
    
