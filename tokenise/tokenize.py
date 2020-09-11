# -*- coding: utf-8 -*-

import sys
import os
import six
import pyonmttok
from tokenizer import tokenizer

################################################
### MAIN #######################################
################################################

if __name__ == '__main__':
    fin = 'stdin'
    fout = 'stdout'
    num_threads = 1
    T = tokenizer()

    usage = """usage: {} [-i FILE -o FILE -num_threads INT]  [tok_options]
    -i: stdin
    -o: stdout
    -num_threads: 1
    -h: this message

  tok_options (See https://github.com/OpenNMT/Tokenizer for more details):
""".format(sys.argv.pop(0),T.tokopts)
    for k,v in T.tokopts.items():
        usage += "    -{}: {}\n".format(k,v)

    while len(sys.argv):
        tok = sys.argv.pop(0)
        if tok=="-h":
            sys.stderr.write("{}\n".format(usage))
            sys.exit()

        if tok[0] == '-':
            tok = tok[1:] ### discard initial '-'
        else:
            sys.stderr.write('error: option {} must be passed with initial \'-\'\n'.format(tok))
            sys.stderr.write("{}\n".format(usage))
            sys.exit()

        if tok in T.opt_strings and len(sys.argv):
    	    T.tokopts[tok] = sys.argv.pop(0)
        elif tok in T.opt_ints and len(sys.argv):
    	    T.tokopts[tok] = int(sys.argv.pop(0))
        elif tok in T.opt_floats and len(sys.argv):
    	    T.tokopts[tok] = float(sys.argv.pop(0))
        elif tok in T.opt_lists and len(sys.argv):
    	    T.tokopts[tok] = sys.argv.pop(0).split(',')
        elif tok in T.opt_bools:
    	    T.tokopts[tok] = True
        elif tok=="i" and len(sys.argv):
            fin = sys.argv.pop(0)
        elif tok=="o" and len(sys.argv):
            fout = sys.argv.pop(0)
        elif tok=="um_threadsn" and len(sys.argv):
            num_threads = int(sys.argv.pop(0))        
        else:
            sys.stderr.write('error: unparsed {} option\n'.format(tok))
            sys.stderr.write("{}\n".format(usage))
            sys.exit()

    if fin == 'stdin' and fout == 'stdout':
        for line in sys.stdin:
            line = str(line.strip('\n'))
            line = T.tokenize_string(line)
            print("{}".format(" ".join(line)))

    elif fin != 'stdin' and fout != 'stdout':
        T.tokenize_file(fin, fout, num_threads)

    else:
        sys.stderr.write('error: options -i/-o must both be used when no stdin/stdout\n')
        sys.stderr.write("{}\n".format(usage))
        sys.exit()
    
