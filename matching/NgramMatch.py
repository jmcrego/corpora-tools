# -*- coding: utf-8 -*-
import sys
from difflib import SequenceMatcher 

class NgramMatch(object):

    def __init__(self, vsrc, vtst, verbose, nline):
        self.verbose = verbose
        if self.verbose:
            print('N: {}'.format(nline))
            print('SRC: {}'.format(' '.join(vsrc)))
            print('TST: {}'.format(' '.join(vtst)))

        self.src = vsrc
        self.tst = vtst
        self.src2tst = [-1] * len(self.src)

    def lcs(self):
        seqMatch = SequenceMatcher(None,self.tst,self.src) 
        match = seqMatch.find_longest_match(0, len(self.tst), 0, len(self.src)) 
        if (match.size!=0): 
            tst_beg = match.a
            tst_end = match.a + match.size
            src_beg = match.b
            src_end = match.b + match.size
            for s in range(match.size):
                self.src2tst[match.b+s] = match.a+s
                if self.verbose:
                    print("[src:{} tst:{}]".format(self.src[match.b+s],self.tst[match.a+s]))
            if self.verbose:
                print("lcs found l={} tst[{},{}] src[{},{}] : {}".format(match.size,tst_beg,tst_end,src_beg,src_end,' '.join(["{}:{}".format(x,self.tst[x]) for x in range(tst_beg, tst_end)])))
            return tst_beg, tst_end, src_beg, src_end
        return 0,0,0,0

