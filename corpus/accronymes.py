# -*- coding: utf-8 -*-
import argparse
import sys
import unicodedata
from collections import defaultdict

def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    only_ascii = nfkd_form.encode('ASCII', 'ignore')
    return str(only_ascii.decode('utf-8'))


class WordIter():

    def __init__(self, wrd, min, max):
        self.wrd = wrd
        self.min = min
        self.max = max

    def indexs2str(self, indexs):
        s = ''.join([self.wrd[i] for i in indexs])
        return s

    def __iter__(self):
        if self.min <= 0:
            yield ''

        list_so_far = [] ### list of lists containing all sequences of indexes of size l
        for i in range(len(self.wrd)):
            list_so_far.append([i])
            yield self.indexs2str([i])
            
        for _ in range(args.maxc-1):
            next_list = []
            for i in range(len(list_so_far)):
                #### i extend now list_so_far[i] with all possible indexes comming after last
                last = list_so_far[i][-1]
                for j in range(last+1,len(self.wrd)):
                    indexs = list(list_so_far[i])
                    indexs.append(j)
                    next_list.append(indexs)
                    if len(indexs) >= args.minc:
                        yield self.indexs2str(indexs)
            list_so_far = next_list



if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--minc", type=int, default=1, help='minimum number of chars in a given word (0)')
    parser.add_argument("--maxc", type=int, default=2, help='maximum number of chars in a given word (3)')
    parser.add_argument("--word", type=str, required=True, help='file with list of valid words')
    parser.add_argument("--remove_diacritics", action='store_true', help='remove diacritics in word file (False)')
    parser.add_argument('str', type=str, help='string with space-separated sequence of words to find accronyms')
    args = parser.parse_args()

    Valid = defaultdict()
    Prefix = defaultdict()
    with open(args.word, encoding="utf8", errors='ignore') as f:
        for w in f:
            w = w.rstrip()
            if args.remove_diacritics:
                w = remove_accents(w)
            Valid[w] = True
            #print(w)
            for l in range(1,len(w)+1):
                Prefix[w[:l]] = True
                #print('\t{}'.format(w[:l]))
                
    sys.stderr.write('found {} valid words\n'.format(len(Valid)))

    W = [WordIter(s,args.minc,args.maxc) for s in args.str.split()]    
    Seen = defaultdict()

    list_so_far = [''] ### list of strings
    for w in range(len(W)):
        sys.stderr.write('Adding strings of word {} with {} strings so_far \n'.format(W[w].wrd, len(list_so_far)))
        next_list = []
        for i in range(len(list_so_far)):
            for s in W[w]:
                if list_so_far[i] + s in Prefix:
                    next_list.append(list_so_far[i] + s)
        list_so_far = next_list

    for s in list_so_far:
        if s in Seen:
            continue
        if s in Valid:
            Seen[s] = True
            print(s)
        
    sys.stderr.write('found {} accronyms\n'.format(len(Seen)))
