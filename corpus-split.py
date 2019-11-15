# -*- coding: utf-8 -*-

import random
import sys

def progress(n):
    if n%10000 == 0:
        if n%100000 == 0:
            sys.stderr.write("{}".format(n))
        else:
            sys.stderr.write(".")

def build_data_set(data,sname,indexs):
    for d in range(len(data)):
        with open(data[d]['name']+'.'+sname, "w") as f:
            for i in indexs:
                f.write(data[d]['lines'][i])    


#####################################################################
### MAIN ############################################################
#####################################################################

if __name__ == '__main__':

    name = sys.argv.pop(0)
    usage = '''usage: {} [-data FILE] [-set INT,STRING]+ [-seed INT] [-v]
   -set STRING,INT : find a set named STRING of INT sentences
   -data      FILE : parallel files to be splitted (all files must contain the same number of sentences)
   -remain  STRING : name for the remaining set (default trn)
   -seed       INT : seed for randomeness (default 0:do not shuffle)
   -v              : verbose output (default False)
Ex: {} -data file.src -data file.tgt -set val,500 -set dev,1000 -set tst,1000 -remain trn
    remaining sentences are stored in file.src.remain and file.tgt.remain
'''.format(name,name)

    seed = 0
    sets = []
    data = []
    remain = 'trn'
    verbose = False
    while len(sys.argv):
        tok = sys.argv.pop(0)
        if tok=="-h":
            sys.stderr.write("{}".format(usage))
            sys.exit()
        elif tok=="-v":
            verbose = True
        elif tok=="-set" and len(sys.argv):
            name,n = sys.argv.pop(0).split(',')
            sets.append({'name':name, 'n':int(n)}) ### name, length
        elif tok=="-data" and len(sys.argv):
            data.append({'name':sys.argv.pop(0)})
        elif tok=="-remain" and len(sys.argv):
            remain = sys.argv.pop(0)
        elif tok=="-seed" and len(sys.argv):
            seed = int(sys.argv.pop(0))
        else:
            sys.stderr.write('error: unparsed {} option\n'.format(tok))
            sys.stderr.write("{}".format(usage))
            sys.exit()

    if len(sets)==0:
        sys.stderr.write('error: missing -set option/s\n')
        sys.stderr.write("{}".format(usage))
        sys.exit()

    if len(data)==0:
        sys.stderr.write('error: missing -data option/s\n')
        sys.stderr.write("{}".format(usage))
        sys.exit()

    for d in range(len(data)):
        #data[d]['lines'] = [line.rstrip('\n') for line in open(data[d]['name'])]
        data[d]['lines'] = [line for line in open(data[d]['name'])]
        if d > 0 and len(data[d]['lines']) != len(data[d-1]['lines']):
            sys.stderr.write('error: diff num of lines in file {}\n'.format(data[d]['name']))
            sys.exit()

    indexs = [x for x in range(len(data[0]['lines']))]
    if seed != 0:
        random.seed(seed)
        random.shuffle(indexs)
        sys.stderr.write('Random seed={}\n'.format(seed))

    from_idx = 0
    for myset in sets:
        to_idx = from_idx + myset['n'] 
        build_data_set(data,myset['name'],indexs[from_idx:to_idx])
        from_idx = to_idx

    if from_idx < len(indexs):
        build_data_set(data,remain,indexs[from_idx:])
