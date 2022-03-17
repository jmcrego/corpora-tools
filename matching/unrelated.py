#coding=utf-8

import sys
import codecs
import argparse
import edit_distance

def related(l1, l2):
    if (len(l1) == 1 and len(l1[0]) == 0) or (len(l2) == 1 and len(l2[0]) == 0):
        return [False] * len(l2)
    sm = edit_distance.SequenceMatcher(a=[s.casefold() for s in l1], b=[s.casefold() for s in l2], action_function=edit_distance.highest_match_action)
    L2 = [False] * len(l2) ### initially all non-related
    for (code, b1, e1, b2, e2) in sm.get_opcodes():
        if code == 'equal':
            L2[b2] = True ### is related
    return L2


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', help='INPUT file (one sentence per line)', required=True)
    parser.add_argument('-s', help='SOURCE file (with sentences similar to those in INPUT file)', required=True)
    parser.add_argument('-t', help='TARGET file (with translations of sentences in SOURCE file)', required=True)
    parser.add_argument('-a', help='ALIGNMENT FILE (word alignments SOURCE/TARGET)', required=True)
    parser.add_argument('-t2s', action='store_true', help='alignments in ALIGNMENT are t-s rather than s-t')
    parser.add_argument('-debug', action='store_true', help='debug mode')
    args = parser.parse_args()

    with codecs.open(args.i, 'r', 'utf-8') as fi, codecs.open(args.s, 'r', 'utf-8') as fs, codecs.open(args.t, 'r', 'utf-8') as ft, codecs.open(args.a, 'r', 'utf-8') as fa:
        for li, ls, lt, la in zip(fi, fs, ft, fa):
            li = li.rstrip().split()
            ls = ls.rstrip().split()
            ls_related = related(li,ls)
            lt = lt.rstrip().split()
            lt_related = [False] * len(lt) ### initially all non-related
            for a in la.rstrip().split():
                s, t = map(int,a.split('-'))
                if args.t2s:
                    s, t = t, s
                if ls_related[s]:
                    lt_related[t] = True

            if args.debug:
                print('I[{}]: {}'.format(len(li),li))
                print('S[{}]: {}'.format(len(ls),ls))
                print('T[{}]: {}'.format(len(lt),lt))
                print('rS[{}]: {}'.format(len(ls_related),ls_related))
                print('rT[{}]: {}'.format(len(lt_related),lt_related))
                    
            out = []
            for i in range(len(lt)):
                if lt_related[i]:
                    out.append(lt[i])
            print(' '.join(out))
