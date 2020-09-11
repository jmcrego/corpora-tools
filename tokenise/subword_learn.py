# -*- coding: utf-8 -*-

import sys
import os
import six
import pyonmttok

def build_tokenizer(args):
    #sys.stderr.write("Options = {}\n".format(args))
    local_args = {}
    for k, v in six.iteritems(args):
        if isinstance(v, six.string_types):
            local_args[k] = v.encode('utf-8')
        else:
            local_args[k] = v
    mode = local_args['mode']
    del local_args['mode']
    return pyonmttok.Tokenizer(mode, **local_args)


def tokenize(tokopts, fin, fout, num_threads):
    t = build_tokenizer(tokopts)

    if fin == 'stdin' and fout == 'stdout':
        for line in sys.stdin:
            line, _ = t.tokenize(str(line.strip('\n')))
            print("{}".format(" ".join(line)))

    elif fin != 'stdin' and fout != 'stdout':
        t.tokenize_file(input_path=fin, output_path=fout, num_threads=num_threads)

    else:
        sys.stderr.write('error: options -i/-o must both be used when no stdin/stdout\n')
        sys.stderr.write("{}\n".format(usage))
        sys.exit()
    
################################################
### MAIN #######################################
################################################

if __name__ == '__main__':

    tokopts = {
        'mode': "conservative",
        'bpe_model_path': "",
        'bpe_dropout': 0.0,
        'vocabulary_path': "",
        'vocabulary_threshold': 0,
        'sp_model_path': "",
        'sp_nbest_size': 0,
        'sp_alpha': 0.1,
        'joiner': "￭",
        'joiner_annotate': False,
        'joiner_new': False,
        'spacer_annotate': False,
        'spacer_new': False,
        'case_feature': False,
        'case_markup': False,
        'no_substitution': False,
        'preserve_placeholders': False,
        'preserve_segmented_tokens': False,
        'segment_case': False,
        'segment_numbers': False,
        'segment_alphabet_change': False,
        'support_prior_joiners': False,
        'segment_alphabet': []
    }
    fin = 'stdin'
    fout = 'stdout'
    num_threads = 1

    usage = """usage: {} [-i FILE -o FILE -num_threads INT]  [tok_options]
    -i: stdin
    -o: stdout
    -num_threads: 1
    -h: this message

  tok_options (See https://github.com/OpenNMT/Tokenizer for more details):
""".format(sys.argv.pop(0),tokopts)
    for k,v in tokopts.items():
        usage += "    -{}: {}\n".format(k,v)

    opt_strings = ['mode','bpe_model_path','vocabulary_path','sp_model_path','joiner']
    opt_ints = ['vocabulary_threshold','sp_nbest_size']
    opt_floats = ['bpe_dropout','sp_alpha']
    opt_lists = ['segment_alphabet']
    opt_bools = ['joiner_annotate','joiner_new','spacer_annotate','spacer_new','case_feature','case_markup','no_substitution','preserve_placeholders','preserve_segmented_tokens','segment_case','segment_numbers','segment_alphabet_change','support_prior_joiners']

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

        if tok in opt_strings and len(sys.argv):
    	    tokopts[tok] = sys.argv.pop(0)
        elif tok in opt_ints and len(sys.argv):
    	    tokopts[tok] = int(sys.argv.pop(0))
        elif tok in opt_floats and len(sys.argv):
    	    tokopts[tok] = float(sys.argv.pop(0))
        elif tok in opt_lists and len(sys.argv):
    	    tokopts[tok] = sys.argv.pop(0).split(',')
        elif tok in opt_bools:
    	    tokopts[tok] = True
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

    tokenize(tokopts, fin, fout, num_threads)
