#!/usr/bin/env python3

import sys
import codecs
import random

def file2list(f):
    with codecs.open(f, 'r', 'utf-8') as fd:
        v = [l for l in fd.read().splitlines()]
    sys.stderr.write('Read {} ~ {} lines\n'.format(f, len(v)))
    return v

#####################################################################
### PARS ############################################################
#####################################################################

if __name__ == '__main__':
    name = sys.argv.pop(0)
    fdb_src = None
    fdb_tgt = None
    fq_src = None
    fq_tgt = None
    fout = None
    p = 0.0
    n = 0
    t = 0.0
    seed = 1234
    inference = False
    fuzzymatch = False
    usage = '''usage: {} -o FILE -db_tgt FILE -q_src FILE -db_src FILE -q_tgt FILE [-p FLOAT] [-n INT] [-l INT] [-t FLOAT] [-inference] [-fuzzymatch] < FILE_QSIM
   -o         FILE : prefix for output files: FILE.src FILE.tgt FILE.sim FILE.pre
   -db_src    FILE : db file with src strings
   -db_tgt    FILE : db file with tgt strings
   -q_src     FILE : query file with src strings
   -q_tgt     FILE : query file with tgt strings
   -p        FLOAT : probability for injecting perfect matchs (default {})
   -n          INT : maximum number of similar sentences used (default {})
   -t        FLOAT : minimum similarity threshold (default {})
   -inference      : test set
   -fuzzymatch     : fuzzy matches (indexs start by 1)
   -seed       INT : seed for randomness (default {})
   -h              : this help
Output:
0.000000      => no match
1.000000      => perfect match
[t, 0.999999] => match
'''.format(name,p,n,t,seed)
    while len(sys.argv):
        tok = sys.argv.pop(0)
        if tok=="-h":
            sys.stderr.write("{}".format(usage))
            sys.exit()
        elif tok=="-inference":
            inference = True
        elif tok=="-fuzzymatch":
            fuzzymatch = True
        elif tok=="-o" and len(sys.argv):
            fout = sys.argv.pop(0)
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
        elif tok=="-p" and len(sys.argv):
            p = float(sys.argv.pop(0))
        elif tok=="-seed" and len(sys.argv):
            seed = int(sys.argv.pop(0))
        else:
            sys.stderr.write('error: unparsed {} option\n'.format(tok))
            sys.stderr.write("{}".format(usage))
            sys.exit()

    print("p={}".format(p))
    print("n={}".format(n))
    print("t={}".format(t))
    print("seed={}".format(seed))
    print('inference={}'.format(inference))
    print('fuzzymatch={}'.format(fuzzymatch))
    random.seed(seed)
    
    if fout is None:
        sys.stderr.write('error: missing -o option\n')
        sys.stderr.write("{}".format(usage))
        sys.exit()

    if fdb_tgt is None:
        sys.stderr.write('error: missing -db_tgt option\n')
        sys.stderr.write("{}".format(usage))
        sys.exit()

    if fdb_src is None:
        sys.stderr.write('error: missing -db_src option\n')
        sys.stderr.write("{}".format(usage))
        sys.exit()
        
    if fq_src is None:
        sys.stderr.write('error: missing -q_src option\n')
        sys.stderr.write("{}".format(usage))
        sys.exit()

    if fq_tgt is None:
        sys.stderr.write('error: missing -q_tgt option\n')
        sys.stderr.write("{}".format(usage))
        sys.exit()
        
    #####################################################################
    ### MAIN ############################################################
    #####################################################################
    DB_src = file2list(fdb_src)
    DB_tgt = file2list(fdb_tgt)
    if len(DB_tgt) != len(DB_src):
        sys.stderr.write('error: different number of lines between {} and {}'.format(DB_src,DB_tgt))
        sys.exit()

    Q_src = file2list(fq_src)
    Q_tgt = file2list(fq_tgt)
    if len(Q_tgt) != len(Q_src):
        sys.stderr.write('error: different number of lines between {} and {}'.format(Q_src,Q_tgt))
        sys.exit()

    fout_src = open(fout + ".src", "w")
    fout_tgt = open(fout + ".tgt", "w")
    fout_pre = open(fout + ".pre", "w")
    fout_sim = open(fout + ".sim", "w")
    fout_num = open(fout + ".num", "w")
    n_out = 0
    n_nomatch = 0
    n_match = 0
    n_perf = 0
    for n_query, l in enumerate(sys.stdin):
        src = Q_src[n_query]
        tgt = Q_tgt[n_query]
        l = l.rstrip()
        toks = l.split('\t') if len(l) else []
        if len(toks) % 2 != 0:
            sys.stderr.write('error: unparsed line {}'.format(l))

        if not inference:
            fout_src.write(src + '\n')
            fout_tgt.write(tgt + '\n')
            fout_sim.write('\n')
            fout_pre.write('\n')
            fout_num.write('{:.6f}\n'.format(0))
            n_out += 1
            n_nomatch += 1
        
            r = random.random()
            if r < p: ### add perfect match
                fout_src.write(src + '\n')
                fout_tgt.write(tgt + '\n')
                fout_sim.write(src + '\n')
                fout_pre.write(tgt + '\n')
                fout_num.write('{:.6f}\n'.format(1))
                n_out += 1
                n_perf += 1

        N = 0
        output = False
        while len(toks):
            score = float(toks.pop(0)) ### most similar sorted first
            if score > 1.0:
                score = 0.999999
            n_db = int(toks.pop(0))
            if fuzzymatch:
                n_db = n_db - 1
            N += 1
            if n_db < 0 or n_db >= len(DB_tgt):
                sys.stderr.write('error: index n_db={} out of bounds'.format(n_db))
                sys.exit()
            if score < t:
                break
            if n > 0 and N > n:
                break            
            fout_src.write(src + '\n')
            fout_tgt.write(tgt + '\n')
            fout_sim.write(DB_src[n_db] + '\n')
            fout_pre.write(DB_tgt[n_db] + '\n')
            fout_num.write('{:.6f}\n'.format(score))
            n_match += 1
            n_out += 1
            output = True
            if inference and output:
                break

        if inference and not output:
            fout_src.write(src + '\n')
            fout_tgt.write(tgt + '\n')
            fout_sim.write('\n')
            fout_pre.write('\n')
            fout_num.write('{:.6f}\n'.format(0.0))
            n_nomatch += 1
            n_out += 1
            
    fout_src.close()
    fout_tgt.close()
    fout_sim.close()
    fout_pre.close()
    sys.stderr.write('Done. Output {} sentences [perfect:{}, match:{} no-match:{}]\n'.format(n_out,n_perf,n_match,n_nomatch))




            
