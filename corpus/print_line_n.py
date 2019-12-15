#!/usr/bin/python -u
# -*- coding: utf-8 -*-
import sys
import os
import glob
import numpy as np
import subprocess
from collections import OrderedDict
prog = sys.argv.pop(0)
if len(sys.argv) < 2 or not sys.argv[-1].isdigit():
    sys.stderr.write('usage: {} [file]+ INT\n'.format(prog))
    sys.exit()
n = int(sys.argv.pop()) ### 0 outputs the last line of files
F = np.concatenate([glob.glob(o) for o in sys.argv])
F = list(OrderedDict.fromkeys(F).keys())
#for f in F: sys.stdout.write('{}\t{}'.format(f,open(f,'r').readlines()[n-1]))
for f in F:
    cmd = "sed '{}q;d' {}".format(n,f)
    getLine = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).stdout #sed "1000q;d" file
    line =  getLine.read().rstrip()

    #cmd = "mapfile -s 100000 -n 1 ary < {}; printf '%s' \"${}ary[0]{}\"".format(f,'{','}')
    #getLine = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).stdout
    #line =  getLine.read().rstrip()
    
    sys.stdout.write('{}\t{}\n'.format(f,line))
