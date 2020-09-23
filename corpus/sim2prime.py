# -*- coding: utf-8 -*-

import sys
import os
import io
import gzip

sep_st      = '\t'
tok_sep     = '※'
tok_curr    = '‖'
tok_range5  = '➎'
tok_range6  = '➏'
tok_range7  = '➐'
tok_range8  = '➑'
tok_range9  = '➒'
tok_range10 = '❿'

def progress(n_line):
    if n_line%10000 == 0:
        if n_line%100000 == 0:
            sys.stderr.write("{}".format(n_line))
        else:
            sys.stderr.write(".")

def read_file(file):
    if file.endswith('.gz'): 
        f = gzip.open(file, 'rb')
        is_gzip = True
    else: 
        f = io.open(file, 'r', encoding='utf-8', newline='\n', errors='ignore')
        is_gzip = False

    vstr = []
    while True:
        l = f.readline()
        if not l:
            break
        if is_gzip:
            l = l.decode('utf8')
        l = l.strip(" \n")
        vstr.append(l)
    return vstr

def get_separator(use_range, score=0.0):
    if not use_range:
        return tok_sep
    if score < 0.5:
        return tok_sep
    elif score >= 0.5 and score < 0.6:
        return tok_range5
    elif score >= 0.6 and score < 0.7:
        return tok_range6
    elif score >= 0.7 and score < 0.8:
        return tok_range7
    elif score >= 0.8 and score < 0.9:
        return tok_range8
    elif score >= 0.9 and score < 1.0:
        return tok_range9
    else: #score >= 1.0:
        return tok_range10


def output_priming(src_similars, tgt_similars, curr_src, curr_tgt, max_length, verbose):

    #case training w/ similars
    #    ※ s'1 s'2 ※ s'1 s'2 s'3 ‖ s1 s2      \t     ※ t'1 t'2 ※ t'1 t'2 t'3 ‖ t1 t2
    #case training w/o similars
    #    <empty sentence>
    #case inference w/ similars
    #    ※ s'1 s'2 ※ s'1 s'2 s'3 ‖ s1 s2      \t     ※ t'1 t'2 ※ t'1 t'2 t'3 ‖
    #case inference w/o similars
    #    s1 s2      \t      

    ### the last src_similars is the most similar to curr_src
    assert len(src_similars) == len(tgt_similars)

    if verbose:
        print('+++++++++++++++++++++++++++++++++')
        print('*** curr_src: {}'.format(curr_src))
        print('*** curr_tgt: {}'.format(curr_tgt))
        print('*** n_similars={}'.format(len(src_similars)))
        print('*** src_sim: ' + '\n*** src_sim: '.join(src_similars))
        print('*** tgt_sim: ' + '\n*** tgt_sim: '.join(tgt_similars))

    is_inference = True if curr_tgt is None else False
    with_similars = False

    src = curr_src
    tgt = curr_tgt if not is_inference else []
    while len(src_similars) and len(tgt_similars) and len(src) <= max_length and len(tgt) <= max_length:
        if len(src)+len(src_similars[0]) > max_length or len(tgt)+len(tgt_similars[0]) > max_length:
            break    
        src = src_similars.pop(0) + src
        tgt = tgt_similars.pop(0) + tgt
        with_similars = True

    if with_similars:
        if verbose:
            print('*** [w similars] lsrc={} ltgt={}'.format(len(src),len(tgt)))
        print(' '.join(src) + sep_st + ' '.join(tgt))

    else: #without_similars
        if verbose:
            print('*** [w/o similars] lsrc={} ltgt={}'.format(len(src),len(tgt)))
        if is_inference: 
            print(' '.join(src[1:]) + sep_st)
        else: #training w/o similars (empty sentence)
            print('')


def output_augment(src_similars, curr_src, curr_tgt, max_length, verbose):

    if verbose:
        print('+++++++++++++++++++++++++++++++++')
        print('*** curr_src: {}'.format(curr_src))
        print('*** curr_tgt: {}'.format(curr_tgt))
        print('*** n_similars={}'.format(len(src_similars)))
        print('*** src_sim: ' + '\n*** src_sim: '.join(src_similars))

    is_inference = True if curr_tgt is None else False
    with_similars = False

    src = curr_src
    tgt = curr_tgt if not is_inference else []
    while len(src_similars) and len(src) <= max_length:
        if len(src)+len(src_similars[0]) > max_length:
            break    
        src = src_similars.pop(0) + src
        with_similars = True

    if with_similars:
        if verbose:
            print('*** [w similars] lsrc={} ltgt={}'.format(len(src),len(tgt)))
        print(' '.join(src) + sep_st + ' '.join(tgt))

    else: #without_similars
        if verbose:
            print('*** [w/o similars] lsrc={} ltgt={}'.format(len(src),len(tgt)))
        if is_inference: 
            print(' '.join(src[1:]) + sep_st)
        else: #training w/o similars (empty sentence)
            print('')


#####################################################################
### MAIN ############################################################
#####################################################################

if __name__ == '__main__':

    n = 1
    t = 0.5
    l = 0
    v = False
    use_range = False
    fuzzymatch = False
    fdb_src = None
    fdb_tgt = None
    fq_src = None
    fq_tgt = None
    name = sys.argv.pop(0)
    usage = '''usage: {} -db_tgt FILE [-db_src FILE] -q_src FILE [-q_tgt FILE] [-range] [-fuzzymatch] [-n INT] [-t FLOAT] [-l INT] [-v] < FSIM > FAUGMENTED
   -db_src   FILE : db file with src strings to output
   -db_tgt   FILE : db file with tgt strings to output
   -q_src    FILE : query file with src strings
   -q_tgt    FILE : query file with tgt strings 
   -range         : use score ranges to separate sentences
   -fuzzymatch    : indexs start by 1
   -n         INT : max n-best similar to output (default 1)
   -t       FLOAT : min threshold to consider (default 0.5)
   -l         INT : max sentence length (default 0)
   -v             : verbose
   -h             : this help

- gzipped files are allowed
- use -q_tgt when preparing training pairs otherwise inference is assumed
- use -db_src for priming 

'''.format(name)

    while len(sys.argv):
        tok = sys.argv.pop(0)
        if tok=="-h":
            sys.stderr.write("{}".format(usage))
            sys.exit()
        elif tok=="-db_src" and len(sys.argv):
            fdb_src = sys.argv.pop(0)
        elif tok=="-db_tgt" and len(sys.argv):
            fdb_tgt = sys.argv.pop(0)
        elif tok=="-q_src" and len(sys.argv):
            fq_src = sys.argv.pop(0)
        elif tok=="-q_tgt" and len(sys.argv):
            fq_tgt = sys.argv.pop(0)
        elif tok=="-n" and len(sys.argv):
            n = int(sys.argv.pop(0))
        elif tok=="-t" and len(sys.argv):
            t = float(sys.argv.pop(0))
        elif tok=="-l" and len(sys.argv):
            l = int(sys.argv.pop(0))
        elif tok=="-v":
            v = True
        elif tok=="-range":
            use_range = True
        elif tok=="-fuzzymatch":
            fuzzymatch = True
        else:
            sys.stderr.write('error: unparsed {} option\n'.format(tok))
            sys.stderr.write("{}".format(usage))
            sys.exit()

    if fdb_tgt is None:
        sys.stderr.write('error: missing -db_tgt option\n')
        sys.stderr.write("{}".format(usage))
        sys.exit()

    if fq_src is None:
        sys.stderr.write('error: missing -q_src option\n')
        sys.stderr.write("{}".format(usage))
        sys.exit()

    ###################
    ### read DB_tgt ###
    ###################
    sys.stderr.write('Reading {}\n'.format(fdb_tgt))
    DB_tgt = read_file(fdb_tgt)
    sys.stderr.write('Read fdb_tgt={} with {} lines\n'.format(fdb_tgt, len(DB_tgt)))

    if fdb_src is not None:
        ###################
        ### read DB_src ###
        ###################
        sys.stderr.write('Reading {}\n'.format(fdb_src))
        DB_src = read_file(fdb_src)
        if len(DB_tgt) != len(DB_src):
            sys.stderr.write('error: erroneous number of lines in fdb_src {}'.format(len(DB_src)))
            sys.exit()
        sys.stderr.write('Read fdb_src={} with {} lines\n'.format(fdb_src, len(DB_src)))

    ##################
    ### read Q_src ###
    ##################
    sys.stderr.write('Reading {}\n'.format(fq_src))
    Q_src = read_file(fq_src)
    sys.stderr.write('Read fq_src={} with {} lines\n'.format(fq_src, len(Q_src)))

    if fq_tgt is not None:
        ##################
        ### read Q_tgt ###
        ##################
        sys.stderr.write('Reading {}\n'.format(fq_tgt))
        Q_tgt = read_file(fq_tgt)
        sys.stderr.write('Read fq_tgt={} with {} lines\n'.format(fq_tgt, len(Q_tgt)))
        if len(Q_tgt) != len(Q_src):
            sys.stderr.write('error: erroneous number of lines in fq_tgt {}'.format(len(Q_tgt)))
            sys.exit()


    #########################################################
    ### augmenting Q_src and Q_tgt with DB_src and DB_tgt ###
    #########################################################
    for n_query, line in enumerate(sys.stdin):
        line = line.rstrip()

        if line == '':
            toks = []
        else:
            toks = line.split('\t')

        if len(toks) % 2 != 0:
            sys.stderr.write('error: unparsed line {}'.format(line))

        src_similars = []
        tgt_similars = []

        ###
        ### add similar sentence/s
        ###########################
        if v:
            print('+++ {}'.format('t'.join(toks)))

        while len(toks):
            score = float(toks.pop(0)) ### similar sentences are sorted by similarity (most similar first)
            n_db = int(toks.pop(0))
            if fuzzymatch: ### fuzzymatch indexs start by 1
                n_db -= 1 

            if score < t:
                break

            tag = get_separator(use_range, score) #+ str(score)
            if fdb_src is not None: ### PRIMING: augment source and target sides
                src_similars.append([tag] + DB_src[n_db].split()) #src_similars[0] is the closest to curr_src
                tgt_similars.append([tag] + DB_tgt[n_db].split())
            else: ### BULTE et al: augment source side with DB_tgt
                src_similars.append([tag] + DB_tgt[n_db].split())

            if len(src_similars) >= n: ### already augmented with n similar sentences
                break

        curr_src = [tok_curr] + Q_src[n_query].split()
        if fq_tgt is not None:
            curr_tgt = [tok_curr] + Q_tgt[n_query].split()
        else:
            curr_tgt = None

        if fdb_src is not None:
            output_priming(src_similars, tgt_similars, curr_src, curr_tgt, l, v)
        else:
            output_augment(src_similars, curr_src, curr_tgt, l, v)



            
