# -*- coding: utf-8 -*-
import sys
import time
import yaml
import string
import pyonmttok
from collections import defaultdict

if (sys.version_info > (3, 0)):
    import pickle
    #sys.stderr.write('python3\n')
else:
    import cPickle as pickle
    #sys.stderr.write('python2\n')

def str_time():
    return time.strftime("[%Y-%m-%d_%X]", time.localtime())

def build_tokenizer():
    local_args = {}
    mode = 'conservative'
    return pyonmttok.Tokenizer(mode, **local_args)

class NgramModel(object):
    def __init__(self, ftrn, N, punct, nums, token):
        self.TAG = '<_t_a_g_>'
        self.N = N
        self.punct = punct
        self.nums = nums
        self.ngram2n = defaultdict(list)
        self.trn = []
        for n, line in enumerate(open(ftrn, 'r')):
            line = line.rstrip()
            #print('{}: {}'.format(n, line))
            if token is not None: 
                toks, _ = token.tokenize(str(line))
            else: 
                toks = line.split()

            toks = self.rewriteTAGS(toks)
            self.trn.append(toks)
            ### saving N-grams
            for i in range(len(toks)-self.N+1):
                seq = ' '.join(toks[i:i+self.N])
                #print('\t{}: {}'.format(i,seq))
                self.ngram2n[seq].append(n)
        sys.stderr.write('{} Distinct {}-grams found: {}\n'.format(str_time(),self.N,len(self.ngram2n)))
        return
                
    def queryfile(self, ftst, maxtags, token):
        self.maxtags = maxtags
        for n, line in enumerate(open(ftst, 'r')):
            line = line.rstrip()
            #print('{}: {}'.format(n, line))
            if token is not None: 
                toks, _ = token.tokenize(str(line))
            else: 
                toks = line.split()
            toks = self.rewriteTAGS(toks)
            ### ntrn is the set of train sentences that contain any of the test N-grams
            ntrn = set()
            for i in range(len(toks)-self.N+1):
                seq = ' '.join(toks[i:i+self.N])
                if seq in self.ngram2n:
                    for n in self.ngram2n[seq]:
                        ntrn.add(n)

            ### find the maximum overlap between tst and all ntrn training sentences
            tst_etoile = '*'+'*'.join(toks)+'*'
            max_overlap = []
            max_n_trn = -1
            for n_trn in ntrn:
                overlap = self.firstLargestOverlap(tst_etoile,self.trn[n_trn])
                if len(overlap) > len(max_overlap):
                    max_overlap = overlap
                    max_n_trn = n_trn

            if len(max_overlap) == 0:
                print('')
                continue
            print("{}\t{}\t{}".format(max_n_trn,len(max_overlap),' '.join(max_overlap)))

        return

    def firstLargestOverlap(self, tst_etoile, trn):
        for l in reversed(range(self.N,len(trn))):
            for i in range(len(trn)-l+1):
                if self.filter_by_tags(trn[i:i+l]):
                    continue
                trnseq_etoile = '*'+'*'.join(trn[i:i+l])+'*'
                if tst_etoile.find(trnseq_etoile) != -1:
                    return trn[i:i+l]
        return []

    def filter_by_tags(self, seq):
        if self.maxtags == -1:
            return False
        n = 0
        for s in seq:
            if s == self.TAG:
                n += 1
                if n > self.maxtags:
                    return True
        return False
        
    def rewriteTAGS(self, toks):
        if not self.punct and not self.nums:
            return toks

            for i in range(len(toks)):
                
                if self.nums and toks[i].replace('.','',1).isdigit():
                    toks[i] = self.TAG
                    continue

                if self.punct:
                    is_punct = True
                    for c in toks[i]:
                        if c not in string.punctuation:
                            is_punct = False
                            break
                    if is_punct:
                        toks[i] = self.TAG
                        continue

        return toks

if __name__ == '__main__':

    name = sys.argv.pop(0)
    usage = '''{}  -trn FILE [-N INT] [-punct] [-nums] | -mod FILE -tst FILE [-maxtags INT]
 Train:
    -trn    FILE : train src file
    -N       INT : minimum N-gram accepted (default 5)
    -punct       : tokens composed (only) of punctuations are rewritten as <_t_a_g_> 
    -nums        : tokens detected as numbers are rewritten as <_t_a_g_> 
 Inference:
    -mod    FILE : model file (contains value used for -N and -punct)
    -tst    FILE : test src file
    -maxtags INT : maximum number of tags to accept a match (default -1:all)

The script needs pyonmttok installed (pip install pyonmttok). mode = 'conservative' is always used!!
Examples:
python {} -trn trn.en -N 5 (build index: trn.en.5gM)
python {} -tst tst.en -mod trn.en.5gM (inference)
'''.format(name,name,name)

    N = 5
    ftrn = None
    fmod = None
    ftst = None
    punct = False
    nums = False
    maxtags = -1
    while len(sys.argv):
        tok = sys.argv.pop(0)
        if   tok=="-mod" and len(sys.argv): fmod = sys.argv.pop(0)
        elif tok=="-tst" and len(sys.argv): ftst = sys.argv.pop(0)
        elif tok=="-trn" and len(sys.argv): ftrn = sys.argv.pop(0)
        elif tok=="-N"   and len(sys.argv): N = int(sys.argv.pop(0))
        elif tok=="-maxtags" and len(sys.argv): maxtags = int(sys.argv.pop(0))
        elif tok=="-punct": punct = True
        elif tok=="-nums": nums = True
        elif tok=="-h":
            sys.stderr.write("{}".format(usage))
            sys.exit()
        else:
            sys.stderr.write('error: unparsed {} option\n'.format(tok))
            sys.stderr.write("{}".format(usage))
            sys.exit()

    if ftrn is None and ftst is None:
        sys.stderr.write('error: either -trn or -tst options must be set\n')
        sys.stderr.write("{}".format(usage))
        sys.exit()

    if ftst is not None and fmod is None:
        sys.stderr.write('error: -tst without -mod option\n')
        sys.stderr.write("{}".format(usage))
        sys.exit()

    sys.stderr.write('{} Start\n'.format(str_time()))
    token = build_tokenizer()

    NM = None
    if ftrn is not None:
        NM = NgramModel(ftrn,N,punct,nums,token)
        fmod = "{}.{}gM".format(ftrn,N)
        if punct:
            fmod = fmod + '_punct'
        if nums:
            fmod = fmod + '_nums'
        with open(fmod, 'wb') as f: pickle.dump(NM, f, pickle.HIGHEST_PROTOCOL)
        sys.stderr.write('{} Write model: {}\n'.format(str_time(),fmod))

    elif ftst is not None:
        #read NM from fmod
        with open(fmod, 'rb') as f: NM = pickle.load(f)
        sys.stderr.write('{} Read model from: {}\n'.format(str_time(),fmod))
        NM.queryfile(ftst,maxtags,token)
        
    sys.stderr.write('{} End\n'.format(str_time()))

