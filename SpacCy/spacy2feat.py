# -*- coding: utf-8 -*-

import sys
name = sys.argv.pop(0)
if len(sys.argv) == 0 or len(sys.argv) > 1:
    sys.stderr.write('usage: {} INT < STDIN > STDOUT\n'.format(name))
    sys.exit()
else:
    feat = int(sys.argv.pop(0))

for l in sys.stdin:
    toks = l.strip().split()
    for i in range(len(toks)):
        feats = toks[i].split('￨')
        if len(feats) < feat:
            sys.stderr.write('not enough features in token {}\n'.format(toks[i]))
            sys.exit()
        toks[i] = feats[feat]
    print(' '.join(toks))
