# -*- coding: utf-8 -*-
import sys
from BilUnits import BilUnits
from NgramMatch import NgramMatch

def writeSentences(fd1, sent1, fd2, sent2, verbose, ntst):
    if len(sent1) != len(sent2):
        sys.stderr.write('error: diff number of tokens when writing f1/f2 {}<>{}\n'.format(len(sent1),len(sent2)))
        sys.exit()
    fd1.write(' '.join(sent1)+'\n')
    fd2.write(' '.join(sent2)+'\n')
    if verbose:
        print("OUTPUT[{}]: {}".format(ntst,' '.join(["{}:{}".format(sent1[x],sent2[x]) for x in range(len(sent1))])))
    return
            
if __name__ == '__main__':

    name = sys.argv.pop(0)
    usage = '''{} -src FILE -tgt FILE -ali FILE [-ml INT] [-v] < 'ntrn TAB tst'
    -src FILE : source file
    -tgt FILE : target file (parallel to src)
    -ali FILE : aligns file (parallel to src)
    -tst FILE : test souirce file
    -sim FILE : matchings file (parallel to tst)
    -col  INT : column in sim file containing the position of the training line, starting by 0 (default 2)
    -out FILE : output files (FILE.f1 .f2)
    -ml   INT : minimum sequence length computed over src file matchings agains tst (default 1)
    -inject   : inject in source rather than repair
    -v        : verbose output

This script requires import NgramMatch
'''.format(name)

    fsrc = None
    ftgt = None
    fali = None
    fout = None
    fsim = None
    ftst = None
    verbose = False
    inject = False
    col = 2
    ml = 1
    while len(sys.argv):
        tok = sys.argv.pop(0)
        if   (tok=="-src" and len(sys.argv)): fsrc = sys.argv.pop(0)
        elif (tok=="-tgt" and len(sys.argv)): ftgt = sys.argv.pop(0)
        elif (tok=="-ali" and len(sys.argv)): fali = sys.argv.pop(0)
        elif (tok=="-sim" and len(sys.argv)): fsim = sys.argv.pop(0)
        elif (tok=="-tst" and len(sys.argv)): ftst = sys.argv.pop(0)
        elif (tok=="-out" and len(sys.argv)): fout = sys.argv.pop(0)
        elif (tok=="-ml"  and len(sys.argv)): ml = int(sys.argv.pop(0))
        elif (tok=="-col" and len(sys.argv)): col = int(sys.argv.pop(0))
        elif (tok=="-inject"): inject = True
        elif (tok=="-v"): verbose = True
        elif (tok=="-h"):
            sys.stderr.write("{}".format(usage))
            sys.exit()
        else:
            sys.stderr.write('error: unparsed {} option\n'.format(tok))
            sys.stderr.write("{}".format(usage))
            sys.exit()

    if fsrc is None or ftgt is None or fali is None or fout is None or fsim is None or ftst is None:
        sys.stderr.write("error: missing some input file argument\n")
        sys.stderr.write("{}".format(usage))
        sys.exit()


    vsrc = [line.rstrip('\n').split() for line in open(fsrc)]
    sys.stderr.write('Read fsrc={} [{}]\n'.format(fsrc,len(vsrc)))
    vtgt = [line.rstrip('\n').split() for line in open(ftgt)]
    sys.stderr.write('Read ftgt={} [{}]\n'.format(ftgt,len(vtgt)))
    vali = [line.rstrip('\n').split() for line in open(fali)]
    sys.stderr.write('Read fali={} [{}]\n'.format(fali,len(vali)))
    if len(vsrc) != len(vtgt) or len(vsrc) != len(vali):
        sys.stderr.write("error: diff number of lines in input src/tgt/ali files\n")
        sys.exit()

    vsim = [line.rstrip('\n') for line in open(fsim)]
    sys.stderr.write('Read fsim={} [{}]\n'.format(fsim,len(vsim)))
    vtst = [line.rstrip('\n').split() for line in open(ftst)]
    sys.stderr.write('Read ftst={} [{}]\n'.format(ftst,len(vtst)))
    if len(vsim) != len(vtst):
        sys.stderr.write("error: diff number of lines in input sim/tst files\n")
        sys.exit()

    f1 = open(fout+'.f1','w')
    f2 = open(fout+'.f2','w')

    for ntst in range(len(vtst)):
        if len(vsim[ntst]) == 0: ### no ngram match
            writeSentences(f1,[],f2,[],verbose,ntst+1)
            continue

        tst = vtst[ntst]
        sim = vsim[ntst].split('\t')
        if len(sim) < col:
            sys.stderr.write('warning: bad input in sim line {}'.format(ntst+1))
            writeSentences(f1,[],f2,[],verbose,ntst+1)
            continue

        ntrn = int(sim[col]) - 1
        if ntrn >= len(vsrc):
            sys.stderr.write("error: index out of bounds ntrn={}\n".format(ntrn))
            sys.exit()

        if verbose:
            print('ntst={}'.format(ntst+1))
            print('ntrn={}'.format(ntrn))
            print('TST: {}'.format(' '.join(tst)))
            print('SRC: {}'.format(' '.join(vsrc[ntrn])))
            print('TGT: {}'.format(' '.join(vtgt[ntrn])))
            print('ALI: {}'.format(' '.join(vali[ntrn])))

        nm = NgramMatch(vsrc[ntrn],tst,verbose,ntst+1)
        tst_beg, tst_end, src_beg, src_end = nm.lcs()
        if src_end - src_beg < ml:
            writeSentences(f1,[],f2,[],verbose,ntst+1)
            continue

        bu = BilUnits(vsrc[ntrn],vtgt[ntrn],vali[ntrn],verbose,ntst+1)
        tuples = bu.tuples_of_src_sequence(src_beg, src_end)
        if len(tuples) == 0:
            writeSentences(f1,[],f2,[],verbose,ntst+1)            
            continue

        if not inject:
            in_match = [] ### contains all the tgt tokens within the ngram match (will be tagged as T, the rest as R)
            for u in tuples:
                for t in u[1]:
                    if t not in in_match:
                        in_match.append(t)

            sent1 = []
            sent2 = []
            for t in tst:
                sent1.append(t)
                sent2.append('S')

            sent1.append('@@@')
            sent2.append('R')

            for i in range(len(vtgt[ntrn])):
                t = vtgt[ntrn][i]
                sent1.append(t)
                if i in in_match:
                    sent2.append('T')
                else:
                    sent2.append('R')

        else:
            tuple_starting_at_s = {} ### tuple starting at s contains [s,s,s],[t,t,t]
            for u in tuples:
                tst_s = []
                for src_s in u[0]:
                    tst_s.append(nm.src2tst[src_s])
                s_first = tst_s[0] ### first tst word in tuple
                tuple_starting_at_s[s_first] = [tst_s,u[1]]

            sent1 = []
            sent2 = []
            seen_i = []
            for i in range(len(tst)):
                if i in seen_i:
                    continue

                if i in tuple_starting_at_s: ### begining of a tuple
                    for tst_i in tuple_starting_at_s[i][0]: ### source words within tuple (tagged as R)
                        sent1.append(tst[tst_i])
                        sent2.append('R')
                        seen_i.append(tst_i)
                    for ti in tuple_starting_at_s[i][1]: ### target words within tuple (tagged as T)
                        sent1.append(vtgt[ntrn][ti])
                        sent2.append('T')
                else:
                    sent1.append(tst[i])
                    sent2.append('S')
                    seen_i.append(i)

        writeSentences(f1,sent1,f2,sent2,verbose,ntst+1)
            
    f1.close()
    f2.close()
