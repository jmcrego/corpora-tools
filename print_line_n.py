#!/usr/bin/python -u
# -*- coding: utf-8 -*-
import sys
import glob
import numpy as np
from collections import OrderedDict
prog = sys.argv.pop(0)
n = int(sys.argv.pop()) ### 0 outputs the last line of files
F = np.concatenate([glob.glob(o) for o in sys.argv])
F = list(OrderedDict.fromkeys(F).keys())
for f in F: sys.stdout.write('{}\t{}'.format(f,open(f,'r').readlines()[n-1]))

