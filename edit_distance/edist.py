# -*- coding: utf-8 -*-
import sys
import edit_distance


class mask_unrelated():

    def __init__(self, u='✖', lc=False):
        self.u = u
        self.lc = lc

    def __call__(self, l1, l2):
        print(l1)
        print(l2)
#        if (len(l1) == 1 and len(l1[0]) == 0) or (len(l2) == 0 and len(l2[0]) == 0):
#            return 0.0, ['EMPTY'], ['EMPTY']

        ### initially all discarded
        L1 = [self.u] * len(l1)
        L2 = [self.u] * len(l2)

        if self.lc: ### use .lower() or .casefold()
            sm = edit_distance.SequenceMatcher(a=[s.casefold() for s in l1], b=[s.casefold() for s in l2], action_function=edit_distance.highest_match_action)
        else:
            sm = edit_distance.SequenceMatcher(a=l1, b=l2, action_function=edit_distance.highest_match_action)

        for (code, b1, e1, b2, e2) in sm.get_opcodes():
            if code == 'equal': ### keep words
                L1[b1] = l1[b1]
                L2[b2] = l2[b2]
        return sm.ratio(), L1, L2

############################################################
### MAIN ###################################################
############################################################

if __name__ == '__main__':
    fa = None
    fb = None
    a = None
    b = None
    u = '✖'
    lc = False
    prog = sys.argv.pop(0)
    usage = '''usage: {} [-fa FILE -fb FILE] [-a STRING -b STRING] [-lc] [-u SRING]
    -fa  FILE : a parallel file to compute unrelated words sentence-by-sentence
    -fb  FILE : b parallel file to compute unrelated words sentence-by-sentence
    -a STRING : a sentences to compute unrelated words
    -b STRING : b sentences to compute unrelated words
    -u STRING : token to mark unrelated words (default {})
    -lc       : lowercase string before computing edit distance (default {})
    -h        : this help
Needs edit_distance module: pip install edit_distance
'''.format(prog,u,lc)
    
    while len(sys.argv):
        tok = sys.argv.pop(0)
        if tok=="-h":
            sys.stderr.write(usage);
            sys.exit()
        elif tok=="-fa":
            fa = sys.argv.pop(0)
        elif tok=="-fb":
            fb = sys.argv.pop(0)
        elif tok=="-a":
            a = sys.argv.pop(0)
        elif tok=="-b":
            b = sys.argv.pop(0)
        else:
            sys.stderr.write('Unrecognized {} option\n'.format(tok))
            sys.stderr.write(usage)
            sys.exit()

    mask = mask_unrelated(u=u, lc=lc)

    if a is not None and b is not None:
        dist, l1, l2 = mask(a.split(' '), b.split(' '))
        print("{:.6f}\t{}\t{}".format(dist,' '.join(l1),' '.join(l2)))

    if fa is not None and fb is not None:
        with open(fa) as f1, open(fb) as f2:
            for a, b in zip(f1, f2):
                dist, l1, l2 = mask(a.strip().split(' '), b.strip().split(' '))
                print("{:.6f}\t{}\t{}".format(dist,' '.join(l1),' '.join(l2)))
