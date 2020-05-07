# -*- coding: utf-8 -*-

import sys
import glob
import subprocess

prog = sys.argv.pop(0)
if len(sys.argv) < 2:
    sys.stderr.write('usage: {} [FILE]+ [INT]+\n'.format(prog))
    sys.stderr.write('  FILE : file to consider (wildcards can be used)\n')
    sys.stderr.write('   INT : line number to output\n')
    sys.exit()

F = []
N = []
while len(sys.argv):
    o = sys.argv.pop(0)
    if o.isdigit():
        N.append(int(o))
    else:
        for f in glob.glob(o):
            F.append(f)
        
for f in F:
    for n in N:
        cmd = "sed '{}q;d' {}".format(n,f)
        getLine = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).stdout #sed "1000q;d" file
        line =  getLine.read().rstrip().decode('utf-8')
        sys.stdout.write('{}[{}]\t{}\n'.format(f,n,line))

    
