#!/usr/bin/python -u
# -*- coding: utf-8 -*-
import sys
import glob
import numpy as np
import os
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
    getLine = subprocess.Popen("sed '{}q;d' {}".format(n,f), shell=True, stdout=subprocess.PIPE).stdout #sed "1000q;d" file
    line =  getLine.read().rstrip()
    sys.stdout.write('{}\t{}\n'.format(f,line))
