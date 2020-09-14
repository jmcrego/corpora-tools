# -*- coding: utf-8 -*-

import sys
import os

augmented_sep     = '※'
augmented_lowest  = '▣'
augmented_range1  = '➊'
augmented_range2  = '➋'
augmented_range3  = '➌'
augmented_range4  = '➍'
augmented_range5  = '➎'
augmented_range6  = '➏'
augmented_range7  = '➐'
augmented_range8  = '➑'
augmented_range9  = '➒'
augmented_range10 = '❿'
augmented_perfect = '◉'
augmented_src     = '⒮'
augmented_tgt     = '⒯'

def progress(n_line):
    if n_line%10000 == 0:
        if n_line%100000 == 0:
            sys.stderr.write("{}".format(n_line))
        else:
            sys.stderr.write(".")

def get_separator(use_range, score=0.0):
    if not use_range:
        return augmented_sep

    if score < 0.5:
        return augmented_wrong
    elif score >= 0.5 and score < 0.55:
        return augmented_range1
    elif score >= 0.55 and score < 0.6:
        return augmented_range2
    elif score >= 0.6 and score < 0.65:
        return augmented_range3
    elif score >= 0.65 and score < 0.7:
        return augmented_range4
    elif score >= 0.7 and score < 0.75:
        return augmented_range5
    elif score >= 0.75 and score < 0.8:
        return augmented_range6
    elif score >= 0.8 and score < 0.85:
        return augmented_range7
    elif score >= 0.85 and score < 0.9:
        return augmented_range8
    elif score >= 0.9 and score < 0.95:
        return augmented_range9
    elif score >= 0.95 and score < 1.0:
        return augmented_range10
    else:
        return augmented_perfect

#####################################################################
### MAIN ############################################################
#####################################################################

if __name__ == '__main__':

    n = 1
    t = 0.5
    use_range = False
    fdb_src = None
    fdb_tgt = None
    fq_src = None
    fq_tgt = None
    sep_st = '\t'
    name = sys.argv.pop(0)
    usage = '''usage: {} -db_tgt FILE [-db_src FILE] -q_src FILE [-q_tgt FILE] [-range] [-n INT] [-t FLOAT] < FSIM > FAUGMENTED
   -db_src FILE : db file with src strings to output
   -db_tgt FILE : db file with tgt strings to output
   -q_src  FILE : query file with src strings
   -q_tgt  FILE : query file with tgt strings
   -range       : use score ranges to separate sentences
   -n       INT : max n-best similar to output (default 1)
   -t     FLOAT : min threshold to consider (default 0.5)
   -h           : this help

- ONLY sentences effectively augmented are output. The rest are left empty
- use -q_tgt when preparing training pairs
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
        elif tok=="-range":
            use_range = True
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
    with open(fdb_tgt,'r') as f:
        DB_tgt = [x.rstrip() for x in f]
    sys.stderr.write('Read fdb_tgt={} with {} lines\n'.format(fdb_tgt, len(DB_tgt)))

    if fdb_src is not None:
        ###################
        ### read DB_src ###
        ###################
        sys.stderr.write('Reading {}\n'.format(fdb_src))
        with open(fdb_src,'r') as f:
            DB_src = [x.rstrip() for x in f]
        if len(DB_tgt) != len(DB_src):
            sys.stderr.write('error: erroneous number of lines in fdb_src {}'.format(len(DB_src)))
            sys.exit()
        sys.stderr.write('Read fdb_src={} with {} lines\n'.format(fdb_src, len(DB_src)))

    ##################
    ### read Q_src ###
    ##################
    sys.stderr.write('Reading {}\n'.format(fq_src))
    with open(fq_src,'r') as f:
        Q_src = [x.rstrip() for x in f]
    sys.stderr.write('Read fq_src={} with {} lines\n'.format(fq_src, len(Q_src)))

    if fq_tgt is not None:
        ##################
        ### read Q_tgt ###
        ##################
        sys.stderr.write('Reading {}\n'.format(fq_tgt))
        with open(fq_tgt,'r') as f:
            Q_tgt = [x.rstrip() for x in f]
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
            print('')
            continue
        
        toks = line.split('\t')
        if len(toks) % 2 != 0:
            sys.stderr.write('error: unparsed line {}'.format(line))

        src_augmented = []
        tgt_augmented = []
        while len(toks):
            score = float(toks.pop(0))
            n_db = int(toks.pop(0))

            if score < t:
                break

            tag = get_separator(use_range, score) #+ str(score)

            if fdb_src is not None: ### augment source and target sides with DB_src and DB_tgt respectively
                src_augmented.append(tag + ' ' + DB_src[n_db])
                tgt_augmented.append(tag + ' ' + DB_tgt[n_db])
            else: ### augment soruce side with DB_tgt
                src_augmented.append(tag + ' ' + DB_tgt[n_db])

            if len(src_augmented) >= n: ### already augmented with n similar sentences
                break

        if len(src_augmented) == 0: ### if not augmented not shown
            print('')
            continue
            
        ### add query sentence/s
        src_augmented.append(augmented_src + ' ' + Q_src[n_query])
        if fq_tgt is not None:
            tgt_augmented.append(augmented_tgt + ' ' + Q_tgt[n_query])
            
        if len(tgt_augmented) == 0:
            print(' '.join(src_augmented))
        else:
            print(' '.join(src_augmented) + '\t' + ' '.join(tgt_augmented))

