# -*- coding: utf-8 -*-

import sys
import os
import six
import glob 
import pyonmttok
import logging
from tokenizer import tokenizer

def create_logger(logfile=None, loglevel='debug'):
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


################################################
### MAIN #######################################
################################################

if __name__ == '__main__':
    fin = []
    fout = None
    symbols = 32000
    min_frequency = 1
    t = tokenizer()

    usage = """usage: {} -o file [-i FILE]+ [-symbols INT] [-min_frequency INT] [tok_options]
    -i: (stdin) [save wildcards for files]
    -o: 
    -symbols: 32000
    -min_frequency: 1
    -h: this message

  tok_options (See https://github.com/OpenNMT/Tokenizer for more details):
""".format(sys.argv.pop(0),t.tokopts)
    for k,v in t.tokopts.items():
        usage += "    -{}: {}\n".format(k,v)

    sys.argv = t.updateOpts(sys.argv)
    while len(sys.argv):
        tok = sys.argv.pop(0)
        if tok=="-h":
            sys.stderr.write("{}\n".format(usage))
            sys.exit()
        elif tok=="-i" and len(sys.argv):
            for f in glob.glob(sys.argv.pop(0)): 
                fin.append(f)
        elif tok=="-o" and len(sys.argv):
            fout = sys.argv.pop(0)
        elif tok=="-symbols" and len(sys.argv):
            symbols = int(sys.argv.pop(0))        
        elif tok=="-min_frequency" and len(sys.argv):
            min_frequency = int(sys.argv.pop(0))        
        else:
            sys.stderr.write('error: unparsed {} option\n'.format(tok))
            sys.stderr.write("{}\n".format(usage))
            sys.exit()

    if fout is None:
        sys.stderr.error('option -o must be used\n')
        sys.stderr.write("{}\n".format(usage))
        sys.exit()        
            
    create_logger()
            
    l = pyonmttok.BPELearner(tokenizer=t.get_tokenizer(), symbols=symbols, min_frequency=min_frequency)

    if len(fin) == 0:
        logging.info('Read stdin')
        for line in sys.stdin:
            l.ingest(str(line.strip('\n')))
    else:
        for f in fin:
            logging.info('Read {}'.format(f))
            l.ingest_file(f)

    logging.info('learning... symbols={} min_frequency={}'.format(symbols, min_frequency))
    l.learn(fout)
    logging.info('Done')
