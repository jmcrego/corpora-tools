# -*- coding: utf-8 -*-

import random
import sys

def progress(n):
    if n%10000 == 0:
        if n%100000 == 0:
            sys.stderr.write("{}".format(n))
        else:
            sys.stderr.write(".")

#####################################################################
### MAIN ############################################################
#####################################################################

if __name__ == '__main__':

    name = sys.argv.pop(0)
    usage = '''usage: {} -i FILE [-v] < indexs.dev_val_tst
   -i FILE : file to split following indexs
   -v      : verbose output (default False)
Ex: {} -i data.en < indexs (creates: data.en.val, data.en.dev, data.en.tst, data.en.trn)
'''.format(name,name)

    fin = None
    verbose = False
    while len(sys.argv):
        tok = sys.argv.pop(0)
        if tok=="-h":
            sys.stderr.write("{}".format(usage))
            sys.exit()
        elif tok=="-v":
            verbose = True
        elif tok=="-i" and len(sys.argv):
            fin = sys.argv.pop(0)
        else:
            sys.stderr.write('error: unparsed {} option\n'.format(tok))
            sys.stderr.write("{}".format(usage))
            sys.exit()

    if fin is None:
        sys.stderr.write('error: missing -i option/s\n')
        sys.stderr.write("{}".format(usage))
        sys.exit()

    indexs = {}
    fd = open("{}.{}".format(fin,'trn'),'w')
    sys.stderr.write("{}.{}\n".format(fin,'trn'))
    fout = {'trn': fd}
    for line in sys.stdin:
        n, name = line.rstrip('\n').split()
        indexs[int(n)] = name
        if name not in fout:
            fd = open("{}.{}".format(fin,name),'w')
            fout[name] = fd
            sys.stderr.write("{}.{}\n".format(fin,name))

    with open(fin) as f: 
        for i,line in enumerate(f): 
            if i in indexs:
                name = indexs[i]
                fout[name].write(line)
            else:
                fout['trn'].write(line)
