import sys
import edit_distance
import difflib

class mask_unrelated():
    def __init__(self, u='✖', lc=False):
        self.u = u
        self.lc = lc

    def __call__(self, l1, l2):
        if self.lc:
            ### use .lower() or .casefold()
            sm = edit_distance.SequenceMatcher(a=[s.casefold() for s in l1], b=[s.casefold() for s in l2], action_function=edit_distance.highest_match_action)
        else:
            sm = edit_distance.SequenceMatcher(a=l1, b=l2, action_function=edit_distance.highest_match_action)

        L1 = [self.u] * len(l1) ### initially all discarded
        L2 = [self.u] * len(l2) ### initially all discarded
        for (code, b1, e1, b2, e2) in sm.get_opcodes():
            if code == 'equal':
                L1[b1] = l1[b1] ### keep word
                L2[b2] = l2[b2] ### keep word
        return sm.ratio(), L1, L2
    
prog = sys.argv.pop(0)
l1 = sys.argv.pop(0).split(' ')
l2 = sys.argv.pop(0).split(' ')
mask = mask_unrelated(lc=True)
dist, l1, l2 = mask(l1,l2)
print(dist)
print(l1)
print(l2)
