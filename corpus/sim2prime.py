# -*- coding: utf-8 -*-

import sys
import os
import io
import random
import gzip
from collections import defaultdict

sep_st      = '\t'
tok_sep     = '⸨sep⸩'
tok_curr    = '⸨cur⸩'
tok_range0  = '⸨0.0⸩'
tok_range1  = '⸨0.1⸩'
tok_range2  = '⸨0.2⸩'
tok_range3  = '⸨0.3⸩'
tok_range4  = '⸨0.4⸩'
tok_range5  = '⸨0.5⸩'
tok_range6  = '⸨0.6⸩'
tok_range7  = '⸨0.7⸩'
tok_range8  = '⸨0.8⸩'
tok_range9  = '⸨0.9⸩'
tok_range10 = '⸨1.0⸩'

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

def get_tag(use_range, score=0.0):
    if not use_range:
        return tok_sep
    elif score < 0.1:
        return tok_range0
    elif score < 0.2:
        return tok_range1
    elif score < 0.3:
        return tok_range2
    elif score < 0.4:
        return tok_range3
    elif score < 0.5:
        return tok_range4
    elif score < 0.6:
        return tok_range5
    elif score < 0.7:
        return tok_range6
    elif score < 0.8:
        return tok_range7
    elif score < 0.9:
        return tok_range8
    elif score < 1.0:
        return tok_range9
    else: 
        return tok_range10

def output_priming(src_similars, tgt_similars, curr_src, curr_tgt, fout_src, fout_tgt, fout_pref, verbose):
    with_similars = True if len(src_similars) else False
    if verbose:
        print('+++++++++++++ PRIMING +++++++++++++')
        print('+++ curr_src: {}'.format(curr_src))
        print('+++ curr_tgt: {}'.format(curr_tgt))
        print('+++ w_similars: {}'.format(with_similars))
        print('+++ src_sim: {}'.format(src_similars))
        print('+++ tgt_sim: {}'.format(tgt_similars))

    if with_similars:
        fout_src.write(' '.join(src_similars + [tok_curr] + curr_src) + '\n')
        if fout_tgt is not None:
            fout_tgt.write(' '.join(tgt_similars + [tok_curr] + curr_tgt) + '\n')
        if fout_pref is not None:
            fout_pref.write(' '.join(tgt_similars + [tok_curr]) + '\n')

    else: #### standard sentence w/o priming
        fout_src.write(' '.join(curr_src) + '\n')
        if fout_tgt is not None:
            fout_tgt.write(' '.join(curr_tgt) + '\n')
        if fout_pref is not None:
            fout_pref.write('\n')

def output_augment(src_similars, curr_src, curr_tgt, fout_src, fout_tgt, verbose):
    with_similars = True if len(src_similars) else False
    if verbose:
        print('------------- AUGMENT -------------')
        print('--- curr_src: {}'.format(curr_src))
        print('--- curr_tgt: {}'.format(curr_tgt))
        print('--- w_similars: {}'.format(with_similars))
        print('--- src_sim: {}'.format(src_similars))

    if with_similars:
        fout_src.write(' '.join(src_similars + [tok_curr] + curr_src) + '\n')
        if fout_tgt is not None:
            fout_tgt.write(' '.join(curr_tgt) + '\n')        

    else: 
        fout_src.write(' '.join(curr_src) + '\n')
        if fout_tgt is not None:
            fout_tgt.write(' '.join(curr_tgt) + '\n')

#####################################################################
### MAIN ############################################################
#####################################################################

if __name__ == '__main__':

    n = 999
    t = 0.0
    l = 999
    pp = 0.0
    v = False
    use_range = False
    fuzzymatch = False
    fdb_src = None
    fdb_tgt = None
    fq_src = None
    fq_tgt = None
    fout = None
    name = sys.argv.pop(0)
    usage = '''usage: {} -o FILE -db_tgt FILE -q_src FILE [-db_src FILE] [-q_tgt FILE] [-range] [-fuzzymatch] [-perfect FLOAT] [-n INT] [-l INT] [-t FLOAT] [-v] < FILE_QSIM
   -o        FILE : FILE.src FILE.pref FILE.tgt files are built
   -db_src   FILE : db file with src strings (PRIMING)
   -db_tgt   FILE : db file with tgt strings
   -q_src    FILE : query file with src strings
   -q_tgt    FILE : query file with tgt strings (TRAINING)
   -range         : use score ranges to separate similar sentences
   -fuzzymatch    : indexs start by 1
   -perfect FLOAT : probability of adding perfect matchs (default 0.0)
   -n         INT : up to n-best similar sentences (default 999)
   -l         INT : max sentence length (default 999)
   -t       FLOAT : min similarity threshold (default 0.0)
   -v             : verbose
   -h             : this help

- use -q_tgt when preparing TRAINING pairs otherwise INFERENCE is assumed
- use -db_src for PRIMING otherwise AUGMENTATION is assumed
- gzipped files are allowed

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
        elif tok=="-o" and len(sys.argv):
            fout = sys.argv.pop(0)
        elif tok=="-n" and len(sys.argv):
            n = int(sys.argv.pop(0))
        elif tok=="-t" and len(sys.argv):
            t = float(sys.argv.pop(0))
        elif tok=="-l" and len(sys.argv):
            l = int(sys.argv.pop(0))
        elif tok=="-perfect" and len(sys.argv):
            pp = float(sys.argv.pop(0))
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

    if fout is None:
        sys.stderr.write('error: missing -o option\n')
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
        is_priming = True
    else:
        is_priming = False

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
        is_inference = False
    else:
        is_inference = True


    fout_src = open(fout + ".src", "w")
    fout_tgt = None if is_inference else open(fout + ".tgt", "w")
    fout_pref = open(fout + ".pref", "w") if is_priming else None

    #########################################################
    ### augmenting Q_src and Q_tgt with DB_src and DB_tgt ###
    #########################################################
    length2n = defaultdict(int)
    tag2n = defaultdict(int)

    for n_query, line in enumerate(sys.stdin):
        line = line.rstrip()

        if line == '':
            toks = []
        else:
            toks = line.split('\t')

        if len(toks) % 2 != 0:
            sys.stderr.write('error: unparsed line {}'.format(line))

        curr_src = Q_src[n_query].split()
        len_curr_src = len(curr_src)
        if is_inference:
            curr_tgt = None
            len_curr_tgt = 0
        else:
            curr_tgt = Q_tgt[n_query].split()
            len_curr_tgt = len(curr_tgt)

        src_similars = []
        tgt_similars = []
        n_similars = 0

        ###
        ### add similar sentence/s
        ###########################

        if random.random() < pp: ### add perfect match
            tag = get_tag(use_range, 1.0)
            if is_priming: ### PRIMING: augment source and target sides
                src_similar = [tag] + curr_src
                tgt_similar = [tag] + curr_tgt
                src_similars = src_similar + src_similars
                tgt_similars = tgt_similar + tgt_similars
                tag2n[tag] += 1
            else: ### AUGMENT: augment source side with DB_tgt (Bulté et al, 2019)
                src_similar = [tag] + curr_tgt
                src_similars = src_similar + src_similars
                tag2n[tag] += 1
            n_similars += 1            

        while len(toks):
            score = float(toks.pop(0)) ### similar sentences are sorted by similarity (most similar first)
            n_db = int(toks.pop(0))

            if score < t:
                break
            if n_similars >= n: ### already augmented n similar sentences
                break
            if fuzzymatch: ### fuzzymatch indexs start by 1
                n_db -= 1 
            if n_db < 0 or n_db >= len(DB_tgt):
                sys.stderr.write('error: index n_db={} out of bounds'.format(n_db))
                sys.exit()

            tag = get_tag(use_range, score)
            if is_priming: ### PRIMING: augment source and target sides
                src_similar = [tag] + DB_src[n_db].split()
                tgt_similar = [tag] + DB_tgt[n_db].split()
                if len(src_similars)+len(src_similar)+len_curr_src+1 > l or len(tgt_similars)+len(tgt_similar)+len_curr_tgt+1 > l: #exceeds max_length
                    continue
                src_similars = src_similar + src_similars
                tgt_similars = tgt_similar + tgt_similars
                tag2n[tag] += 1

            else: ### AUGMENT: augment source side with DB_tgt (Bulté et al, 2019)
                src_similar = [tag] + DB_tgt[n_db].split()
                if len(src_similars)+len(src_similar)+len_curr_src+1 > l: #exceeds max_length
                    continue
                src_similars = src_similar + src_similars
                tag2n[tag] += 1

            n_similars += 1

        #if n_similars not in length2n:
        #    length2n[n_similars] = 0
        length2n[n_similars] += 1
        ### output
        if is_priming:
            output_priming(src_similars, tgt_similars, curr_src, curr_tgt, fout_src, fout_tgt, fout_pref, v)
        else:
            output_augment(src_similars, curr_src, curr_tgt, fout_src, fout_tgt, v)

    fout_src.close()
    if not is_inference:
        fout_tgt.close()
    if is_priming:
        fout_pref.close()

    sys.stderr.write('Done\n')
    for l, n in sorted(length2n.items()):
        sys.stderr.write('{}-similars => {}\n'.format(l,n))
    for l, n in sorted(tag2n.items()):
        sys.stderr.write('{}-tag => {}\n'.format(l,n))

            
