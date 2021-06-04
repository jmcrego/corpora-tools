#!/usr/bin/python

#conda install -c conda-forge spacy
#python -m spacy download en_core_web_md
#python -m spacy download fr_core_news_md
#python -m spacy download es_core_news_md

import sys
import time
import spacy

def analyse(BUCKET):
    m = 0
    docs = list(nlp.pipe(BUCKET))
    for doc in docs: 
        toks = []
        for token in doc:
            m += 1
            toks.append("{}￨{}￨{}￨{}".format(token.text.replace(' ','▁'), token.lemma_.replace(' ','▁'), token.pos_, token.morph)) #token.tag_, #token.dep_, #token.shape_, #token.is_alpha, #token.is_stop
        print(' '.join(toks))
    return m

##########################################################################################
### MAIN #################################################################################
##########################################################################################

name = sys.argv.pop(0)
if len(sys.argv) == 0 or len(sys.argv) > 1:
    sys.stderr.write('usage: {} lang < STDIN > STDOUT\n'.format(name))
    sys.exit()
else:
    lang = sys.argv.pop(0)
    
if lang == 'en':
    nlp = spacy.load("en_core_web_md",  disable=["parser"])
elif lang == 'fr':
    nlp = spacy.load("fr_core_news_md", disable=["parser"])
elif lang == 'es':
    nlp = spacy.load("es_core_news_md", disable=["parser"])
else:
    sys.stderr.write('only en, fr, es languages supported!\n')
    sys.exit()
    
tic = time.time()
n = 0
m = 0
bucket_size = 1000
BUCKET = []
for l in sys.stdin:
    n += 1
    if len(BUCKET) == bucket_size:
        m += analyse(BUCKET)
        BUCKET = []
    BUCKET.append(l.strip())
if len(BUCKET):
    m += analyse(BUCKET)
toc = time.time()
sys.stderr.write('Analysed {} sentences {} tokens in {:.3f} seconds [{:.1f} toks/sec, {:.1f} sents/sec]\n'.format( n, m, toc-tic, m/(toc-tic), n/(toc-tic) ))


