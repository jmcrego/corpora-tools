# -*- coding: utf-8 -*-

import sys
import io
import math
from time import time
import spacy
import logging

def create_logger(logfile, loglevel):
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        sys.stderr.write("Invalid log level={}\n".format(loglevel))
        sys.exit()
    if logfile is None or logfile == 'stderr':
        logging.basicConfig(format='[%(asctime)s.%(msecs)03d] %(levelname)s %(message)s', datefmt='%Y-%m-%d_%H:%M:%S', level=numeric_level)
        logging.info('Created Logger level={}'.format(loglevel))
    else:
        logging.basicConfig(filename=logfile, format='[%(asctime)s.%(msecs)03d] %(levelname)s %(message)s', datefmt='%Y-%m-%d_%H:%M:%S', level=numeric_level)
        logging.info('Created Logger level={} file={}'.format(loglevel, logfile))

def length_component(doc):
    print("Doc length:", len(doc)) # Print the doc's length
    return doc # Return the doc object

class Args():

    def __init__(self, argv):
        self.data = 'stdin'
        self.model = 'en'
        self.joiner = '￨'
        self.log_file = 'stderr'
        self.log_level = 'info'
        self.ents = False
        self.NPs = False
        self.bucket = 1000
        self.prog = argv.pop(0)
        self.usage = '''usage: {} [-model MODEL] [-data FILE] [-joiner STRING] [-bucket_size INT] [-ents] [-NPs] [-log_file FILE] [log_level LEVEL]
   -data       FILE : input file                            (stdin)
   -model     MODEL : spacy model                           (en) [equivalent to en_core_web_sm]
   -joiner   STRING : string to join linguistic features    (￨)
   -bucket      INT : bucket size                           (1000)
   -ents            : output entities                       (False)
   -NPs             : output NPs                            (False) if used, activates parsing
   -log_file   FILE : log file (use stderr for STDERR)      (stderr)
   -log_level LEVEL : debug, info, warning, critical, error (debug) 
   -h               : this help

*** The script needs:
  + pip install -U spacy
  + spacy download en (or any other available model to use: fr, es, de, ...) (same as: python -m spacy download en)
  - use: spacy info (to check the models installed)
'''.format(self.prog)

        while len(argv):
            tok = argv.pop(0)
            if (tok=="-joiner" and len(argv)): self.joiner = argv.pop(0)
            elif (tok=="-data" and len(argv)): self.data = argv.pop(0)
            elif (tok=="-model" and len(argv)): self.model = argv.pop(0)
            elif (tok=="-bucket" and len(argv)): self.bucket = int(argv.pop(0))
            elif (tok=="-log_file" and len(argv)): self.log_file = argv.pop(0)
            elif (tok=="-log_level" and len(argv)): self.log_level = argv.pop(0)
            elif (tok=="-ents"):
                self.ents = True
            elif (tok=="-NPs"):
                self.NPs = True
            elif (tok=="-h"):
                sys.stderr.write("{}".format(self.usage))
                sys.exit()
            else:
                sys.stderr.write('error: unparsed {} option\n'.format(tok))
                sys.stderr.write("{}".format(self.usage))
                sys.exit()

        create_logger(self.log_file, self.log_level)


if __name__ == "__main__":

    args = Args(sys.argv) #creates logger
    if args.NPs:
        nlp = spacy.load(args.model)
    else:
        nlp = spacy.load(args.model, disable=["parser"])
        
    logging.info('pipeline: {}'.format(nlp.pipe_names)) #print(nlp.pipeline)

    TEXTS = []
    if args.data is not 'stdin':
        with open(args.data) as f:
            TEXTS = f.read().splitlines()
    else:
        for l in sys.stdin:
            TEXTS.append(l.rstrip())

    nbuckets = math.ceil(len(TEXTS) / args.bucket)
    nlines = len(TEXTS)
    logging.info('read {} with {} lines, {} buckets'.format(args.data, nlines, nbuckets))

    tic = time()
    nbucket = 0
    nline = 0
    while len(TEXTS):
        nbucket += 1        
        if len(TEXTS) >= args.bucket:
            BUCKET = TEXTS[:args.bucket]
            del TEXTS[:args.bucket]
        else:
            BUCKET = list(TEXTS)
            del TEXTS[:len(TEXTS)]
    
        docs = list(nlp.pipe(BUCKET))
        while len(docs): ### docs are lines
            nline += 1
            doc = docs.pop(0)
            sentence = []
            start_char2i = {}
            end_char2i = {}
            for i,token in enumerate(doc):
                start_char2i[token.idx] = token.i
                feats = []
                if token.i != i:
                    logging.error('token.i != i in line {}'.format(nline))
                #feats.append(str(token.i))
                feats.append(token.text)
                #feats.append(token.lemma_)
                #feats.append(token.tag_)
                feats.append(token.pos_)
                #feats.append(token.dep_)
                #feats.append(token.ent_iob_)
                #feats.append(token.ent_type_)
                ### add token to sentence
                sentence.append(args.joiner.join(feats))

            oline = ' '.join(sentence)

            if args.ents:
                for ent in doc.ents:
                    i = start_char2i[ent.start_char]
                    oline += "\t" + "Ent[{},{}]:{} {}".format(i, i + len(ent.text.split()) - 1, ent.label_, ent.text)
                
            if args.NPs:
                for chk in doc.noun_chunks:
                    i = start_char2i[chk.start_char]
                    oline += "\t" + "NP[{},{}] {}".format(i, i + len(chk.text.split()) - 1, chk.text)
            
            print(oline)

        logging.info('processed {}/{} lines, {}/{} buckets'.format(nline, nlines, nbucket, nbuckets))
    toc = time()
    logging.info('End ({:.2f} seconds)'.format(toc-tic))
