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

# this should be local to a document (i.e., topic part), so reset it as needed by calling reset_link_string()

def reset_link_string():
    global link_string, no_link_string
    link_string = defaultdict(str)
    no_link_string = set()
    # we predefine some common abbreviations that have problems
    # our simple matcher links USA to Usa, a city in Japan :-(
    link_string['USA'] = "United States of America"
    link_string['U.S.'] = "United States of America"
    
reset_link_string()

def find_link_strings(doc):
    """ checks entity mentions of types PERSON and ORG to predict coreference; checks defined abbreviations.
        link_stringsd has keys and vlaues which are mention strings.  SHiould be be tuples, string and type? """
    
    global link_string
    
    for abrv in doc._.abbreviations:
        # use the abbreviation pipe data
        #print(f"link string {abrv} ==> {abrv._.long_form} ")
        link_string[abrv.text] = abrv._.long_form.text
    
    # may be risky to match an ORG with a PER
    for e in doc.ents:
        #print("CHecking ent", e)
        # find a single token PER or ORG
        if e.end - e.start > 1 or e.label_  not in ['PERSON', 'ORG']: continue
        etl = (e.text, e.label_)
        etext = trim(e.text)
        if etext in link_string: continue
        #print(f"Checking possible coref {etl}")
        matches = []
        for e2 in doc.ents:
            # only consider a multi-token PER
            if e == e2 or e2.label_ != 'PERSON' or e2.end - e2.start == 1 :
                continue
            #print(f"Compare {etext} to {first_last(e2)}")
            if etext in first_last(e2):
                matches.append(trim(e2.text))
        # we have winner if there's one and only one match
        if matches and matches.count(matches[0]) == len(matches):
            link_string[etext] = matches[0]
            #print(f"Coref {etl} to {matches[0]}")
        #else:
            # we don't what to check this twice in document
            #no_link_string.add(etext)

    for e in doc.ents:
        # for a one word entity that looks like an abbreviation, look for an extended version
        if e.end - e.start == 1 and e.label_ in ['ORG', 'LAW'] and e.text.isupper() and 1 < len(e.text) < 8:
            etl = (e.text, e.label_)
            if e.text in link_string  or (e.text in no_link_string):
                continue
            #print(f"Checking possible abbreviation {etl}")
            matches = [ ]
            # match mentions that yield a plausible abbreviation
            for e2 in doc.ents:
                if e != e2 and e2.label_ == e.label_ :
                    e2tokens =  re.split(' |-', e2.text)
                    if e2tokens[0] in ["The", "the", "a", "an", "A", "An"]:
                        #print('trimming', e2tokens[0])
                        e2tokens = e2tokens[1:]
                    if len(e2tokens) > len(e.text):
                        e2tokens = [t for t in e2tokens if t not in ['of', 'for', 'and', 'in', 'with', 'on', '&']]
                        #print(e2tokens)
                        if len(e2tokens) != len(e.text):
                            continue
                    else:
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
                link_string[e.text] = matches[0]
                #print(f"Coref {etl}  to {matches[0]}")
            else:
                #print(f"adding {etl} to no_link_string")
                no_link_string.add(e.text)




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
    
def first_last(e):
    """ return list of first and last names in a multi-token name, trimmed  """
    tokens = e.text.split(' ')
    return [trim(tokens[0]), trim(tokens[-1])]

