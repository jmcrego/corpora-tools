# -*- coding: utf-8 -*-

import sys
import io
#import glob
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
        self.prog = argv.pop(0)
        self.usage = '''usage: {} [-model MODEL] [-data FILE] [-joiner STRING] [-log_file FILE] [log_level LEVEL]
   -data       FILE : input file                            (stdin)
   -model     MODEL : spacy model                           (en) [equivalent to en_core_web_sm]
   -joiner   STRING : string to join linguistic features    (￨)
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
            elif (tok=="-log_file" and len(argv)): self.log_file = argv.pop(0)
            elif (tok=="-log_level" and len(argv)): self.log_level = argv.pop(0)
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
    #nlp = spacy.load(args.model, disable=["parser"])
    nlp = spacy.load(args.model)
    #nlp.add_pipe(length_component, first=True) # Add the component first in the pipeline

    logging.info('pipeline: {}'.format(nlp.pipe_names)) #print(nlp.pipeline)

    TEXTS = []
    if args.data is not 'stdin':
        with open(args.data) as f:
            TEXTS = f.read().splitlines()
    else:
        for l in sys.stdin:
            TEXTS.append(l.rstrip())
    logging.info('read {} with {} lines'.format(args.data,len(TEXTS)))

    docs = list(nlp.pipe(TEXTS))
    logging.info('processed {} lines'.format(len(docs)))

    while len(docs):
        doc = docs.pop(0)
        sentence = []
        start_char2i = {}
        end_char2i = {}
        for token in doc:
            start_char2i[token.idx] = token.i
            feats = []
            feats.append(str(token.i))
            feats.append(token.text)
            feats.append(token.lemma_)
            feats.append(token.tag_)
            #feats.append(token.pos_)
            #feats.append(token.dep_)
            #feats.append(token.ent_iob_)
            #feats.append(token.ent_type_)
            sentence.append(args.joiner.join(feats))

        Ents = []
        for ent in doc.ents:
            i = start_char2i[ent.start_char]
            Ents.append("Ent:{}[{},{}] {}".format(ent.label_, i, i + len(ent.text.split()) - 1, ent.text))

        NPs = []
        for chk in doc.noun_chunks:
            i = start_char2i[chk.start_char]
            NPs.append("NP[{},{}] {}".format(i,i + len(chk.text.split()) - 1, chk.text))
            
        print(' '.join(sentence) + '\t' + '\t'.join(Ents) + '\t' + '\t'.join(NPs))

