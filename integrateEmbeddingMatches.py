# -*- coding: utf-8 -*-
import sys

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
    usage = '''{} -src FILE -tgt FILE -tst FILE -sim FILE -out FILE [-v]'
    -src FILE : source file
    -tgt FILE : target file
    -tst FILE : test souirce file
    -sim FILE : matchings file (parallel to tst)
    -out FILE : output files (FILE.f1 .f2)
    -v        : verbose output

This script requires import NgramMatch
'''.format(name)

    fsrc = None
    ftgt = None
    fout = None
    fsim = None
    ftst = None
    verbose = False
    while len(sys.argv):
        tok = sys.argv.pop(0)
        if   (tok=="-src" and len(sys.argv)): fsrc = sys.argv.pop(0)
        elif (tok=="-tgt" and len(sys.argv)): ftgt = sys.argv.pop(0)
        elif (tok=="-sim" and len(sys.argv)): fsim = sys.argv.pop(0)
        elif (tok=="-tst" and len(sys.argv)): ftst = sys.argv.pop(0)
        elif (tok=="-out" and len(sys.argv)): fout = sys.argv.pop(0)
        elif (tok=="-v"): verbose = True
        elif (tok=="-h"):
            sys.stderr.write("{}".format(usage))
            sys.exit()
        else:
            sys.stderr.write('error: unparsed {} option\n'.format(tok))
            sys.stderr.write("{}".format(usage))
            sys.exit()

    if fsrc is None or fout is None or fsim is None or ftst is None:
        sys.stderr.write("error: missing some input file argument\n")
        sys.stderr.write("{}".format(usage))
        sys.exit()


    vsrc = [line.rstrip('\n').split() for line in open(fsrc)]
    sys.stderr.write('Read fsrc={} [{}]\n'.format(fsrc,len(vsrc)))
    vtgt = [line.rstrip('\n').split() for line in open(ftgt)]
    sys.stderr.write('Read ftgt={} [{}]\n'.format(ftgt,len(vtgt)))
    vsim = [line.rstrip('\n') for line in open(fsim)]
    sys.stderr.write('Read fsim={} [{}]\n'.format(fsim,len(vsim)))
    vtst = [line.rstrip('\n').split() for line in open(ftst)]
    sys.stderr.write('Read ftst={} [{}]\n'.format(ftst,len(vtst)))

    i_tst2i_tgt = {}
    for i in range(len(vsim)):
        t = vsim[i].split('\t')
        i_tst = int(t[0])
        i_tgt = int(t[2])
        if i_tgt >= len(vtgt):
            sys.stderr.write("error: i_tgt={} out of bounds len(vtgt)={}\n".format(i_tgt,len(vtgt)))
            sys.exit()
        i_tst2i_tgt[i_tst] = i_tgt

    f1 = open(fout+'.f1','w')
    f2 = open(fout+'.f2','w')

    for i_tst in range(len(vtst)):
        if i_tst not in i_tst2i_tgt:
            writeSentences(f1,[],f2,[],False,i_tst)
        else:
            tst_tgt_f1 = vtst[i_tst]
            tst_tgt_f2 = ['S' for i in range(len(tst_tgt_f1))]

            tst_tgt_f1.append('@@@')
            tst_tgt_f2.append('E')

            for t in vtgt[i_tst2i_tgt[i_tst]]:
                tst_tgt_f1.append(t)
                tst_tgt_f2.append('E')

            writeSentences(f1,tst_tgt_f1,f2,tst_tgt_f2,False,len(tst_tgt_f1))
            
    f1.close()
    f2.close()
