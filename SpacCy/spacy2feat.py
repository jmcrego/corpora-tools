# -*- coding: utf-8 -*-

import sys
name = sys.argv.pop(0)
if len(sys.argv) == 0 or len(sys.argv) > 1:
    sys.stderr.write('usage: {} INT < STDIN > STDOUT\n'.format(name))
    sys.exit()
else:
    feat = int(sys.argv.pop(0))

nline = 0
for l in sys.stdin:
    nline += 1
    toks = l.strip().split()
    for i in range(len(toks)):
        #print('tok: {}'.format(toks[i]))
        feats = toks[i].split('￨')
        #print('feats: {}'.format(feats))
        if feat >= len(feats):
            sys.stderr.write('not enough features in token {} of line {}\n'.format(toks[i], nline))
            toks[i] = '-'
        elif len(feats[feat]):
            toks[i] = feats[feat]
        else:
            toks[i] = '-'
    print(' '.join(toks))
