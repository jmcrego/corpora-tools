# -*- coding: utf-8 -*-

import sys
import os
import six
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
    fin = None
    fout = None
    num_threads = 1
    t = tokenizer()

    usage = """usage: {} [-i FILE -o FILE -num_threads INT]  [tok_options]
    -i: (stdin)
    -o: (stdout)
    -num_threads: 1 (used only when -i and -o are used)
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
            fin = sys.argv.pop(0)
        elif tok=="-o" and len(sys.argv):
            fout = sys.argv.pop(0)
        elif tok=="-num_threads" and len(sys.argv):
            num_threads = int(sys.argv.pop(0))        
        else:
            sys.stderr.write('error: unparsed {} option\n'.format(tok))
            sys.stderr.write("{}\n".format(usage))
            sys.exit()

    create_logger()
    t.build_tokenizer()
    
    if fin is not None and fout is not None:
        logging.info('Reading {} writing {}'.format(fin,fout))
        t.tokenize_file(fin, fout, num_threads)

    else:
        logging.info('Reading stdin writing stdout')
        for line in sys.stdin:
            line = t.tokenize_line(str(line.strip('\n')))
            print("{}".format(" ".join(line)))
            
    logging.info('Done')
