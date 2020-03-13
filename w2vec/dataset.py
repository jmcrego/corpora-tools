
import logging
import yaml
import sys
import os
import io
import math
import glob
import gzip
import random
import itertools
import pyonmttok
import numpy as np
from collections import defaultdict, Counter

def open_file_read(file):
    logging.info('reading: {}'.format(file))
    if file.endswith('.gz'): 
        f = gzip.open(file, 'rb')
        is_gzip = True
    else: 
        f = io.open(file, 'r', encoding='utf-8', newline='\n', errors='ignore')
        is_gzip = False
    return f, is_gzip

####################################################################
### OpenNMTTokenizer ###############################################
####################################################################
class OpenNMTTokenizer():

    def __init__(self, fyaml):
        opts = {}
        if fyaml is None:
            self.tokenizer = None
        else:
            with open(fyaml) as yamlfile: 
                opts = yaml.load(yamlfile, Loader=yaml.FullLoader)

            if 'mode' not in opts:
                logging.error('error: missing mode in tokenizer')
                sys.exit()

            mode = opts["mode"]
            del opts["mode"]
            self.tokenizer = pyonmttok.Tokenizer(mode, **opts)
            logging.info('built tokenizer mode={} {}'.format(mode,opts))

    def tokenize(self, text):
        if self.tokenizer is None:
            tokens = text.split()
        else:
            tokens, _ = self.tokenizer.tokenize(text)
        return tokens

    def detokenize(self, tokens):
        if self.tokenizer is None:
            return tokens
        return self.tokenizer.detokenize(tokens)

####################################################################
### Vocab ##########################################################
####################################################################
class Vocab():

    def __init__(self):
        self.idx_unk = 0 
        self.str_unk = '<unk>'
        self.tok_to_idx = {} 
        self.idx_to_tok = [] 

    def read(self, file):
        f, is_gzip = open_file_read(file)
        for l in f:
            if is_gzip:
                l = l.decode('utf8')
            tok = l.strip(' \n')
            if tok not in self.tok_to_idx:
                self.idx_to_tok.append(tok)
                self.tok_to_idx[tok] = len(self.tok_to_idx)
        f.close()
        logging.info('read vocab ({} entries) from {}'.format(len(self.idx_to_tok),file))

    def dump(self, file):
        f = open(file, "w")
        for tok in self.idx_to_tok:
            f.write(tok+'\n')
        f.close()
        logging.info('written vocab ({} entries) into {}'.format(len(self.idx_to_tok),file))

    def build(self,files,token,min_freq=5,max_size=0):
        self.tok_to_frq = defaultdict(int)
        for file in files:
            f, is_gzip = open_file_read(file)
            for l in f:
                if is_gzip:
                    l = l.decode('utf8')                
                for tok in token.tokenize(l.strip(' \n')):
                    self.tok_to_frq[tok] += 1
            f.close()
        self.tok_to_idx[self.str_unk] = self.idx_unk
        self.idx_to_tok.append(self.str_unk)
        for wrd, frq in sorted(self.tok_to_frq.items(), key=lambda item: item[1], reverse=True):
            if len(self.idx_to_tok) == max_size:
                break
            if frq < min_freq:
                break
            self.tok_to_idx[wrd] = len(self.idx_to_tok)
            self.idx_to_tok.append(wrd)
        logging.info('built vocab ({} entries) from {}'.format(len(self.idx_to_tok),files))

    def __len__(self):
        return len(self.idx_to_tok)

    def __iter__(self):
        for tok in self.idx_to_tok:
            yield tok

    def __contains__(self, s): ### implementation of the method used when invoking : entry in vocab
        if type(s) == int: ### testing an index
            return s>=0 and s<len(self)
        ### testing a string
        return s in self.tok_to_idx

    def __getitem__(self, s): ### implementation of the method used when invoking : vocab[entry]
        if type(s) == int: ### input is an index, i want the string
            if s not in self:
                logging.error("key \'{}\' not found in vocab".format(s))
                sys.exit()
            return self.idx_to_tok[s]
        ### input is a string, i want the index
        if s not in self: 
            return self.idx_unk
        return self.tok_to_idx[s]

####################################################################
### Dataset ########################################################
####################################################################
class Dataset():

    def __init__(self, files, token, vocab, batch_size=128, window=5, n_negs=10, skip_subsampling=True):
        self.batch_size = batch_size
        self.vocab_size = len(vocab)
        self.window = window
        self.n_negs = n_negs
        self.idx_pad = vocab.idx_unk ### no need for additional token in vocab
        self.corpus = []
        self.wrd2n = defaultdict(int)
        ntokens = 0
        nOOV = 0
        for file in files:
            f, is_gzip = open_file_read(file)
            for l in f:
                if is_gzip:
                    l = l.decode('utf8')
                toks = token.tokenize(l.strip(' \n'))
                self.corpus.append([])
                for tok in toks:
                    idx = vocab[tok]
                    if idx == vocab.idx_unk:
                        nOOV += 1
                    self.corpus[-1].append(idx)
                    self.wrd2n[idx] += 1
                ntokens += len(toks)
            f.close()
        pOOV = 100.0 * nOOV / ntokens
        logging.info('read {} sentences with {} tokens (%OOV={:.2f}) [batch_size={}, window={}, n_negs={}, skip_subsampling={}]'.format(len(self.corpus),ntokens,pOOV,batch_size,window,n_negs,skip_subsampling))
        ### subsample
        if not skip_subsampling:
            ntokens = self.SubSample(ntokens)
            logging.info('subsampled to {} tokens'.format(ntokens))

    def __iter__(self):
#        NS = self.NegativeSamples()
        indexs = [i for i in range(len(self.corpus))]
        random.shuffle(indexs)
        batch_wrd = []
        batch_ctx = []
        batch_neg = []
        for index in indexs:
            toks = self.corpus[index]
            for i in range(len(toks)):
                wrd = toks[i]
                ctx = []
                for j in range(i-self.window,i+self.window+1):
                    if j<0:
                        ctx.append(self.idx_pad)
                    elif j>=len(toks):
                        ctx.append(self.idx_pad)
                    elif j!=i:
                        ctx.append(toks[j])
#                neg = next(NS)
#                neg = [random.randint(1, len(self.wrd2n)) for _ in range(self.neg_samples)]
                neg = []
                for _ in range(self.n_negs):
                    idx = wrd
                    while idx in ctx or idx == wrd:
                        idx = random.randint(1, self.vocab_size-1)
                    neg.append(idx)

                batch_wrd.append(wrd)
                batch_ctx.append(ctx)
                batch_neg.append(neg)
                if len(batch_wrd) == self.batch_size:
                    yield [batch_wrd, batch_ctx, batch_neg]
                    batch_wrd = []
                    batch_ctx = []
                    batch_neg = []
        if len(batch_wrd):
            yield [batch_wrd, batch_ctx, batch_neg]

    def SubSample(self, sum_counts):
#        wrd2n = dict(Counter(list(itertools.chain.from_iterable(self.corpus))))
        wrd2p_keep = {}
        for wrd in self.wrd2n:
            p_wrd = float(self.wrd2n[wrd]) / sum_counts ### proportion of the word
            p_keep = 1e-3 / p_wrd * (1 + math.sqrt(p_wrd * 1e3)) ### probability to keep the word
            wrd2p_keep[wrd] = p_keep

        filtered_corpus = []
        ntokens = 0
        for toks in self.corpus:
            filtered_corpus.append([])
            for wrd in toks:
                if random.random() < wrd2p_keep[wrd]:
                    filtered_corpus[-1].append(wrd)
                    ntokens += 1

        self.corpus = filtered_corpus
        return ntokens

    def NegativeSamples(self):
#        wrd2n = dict(Counter(list(itertools.chain.from_iterable(self.corpus))))
        normalizing_factor = sum([v**0.75 for v in self.wrd2n.values()])
        sample_probability = {}
        for wrd in self.wrd2n:
            sample_probability[wrd] = self.wrd2n[wrd]**0.75 / normalizing_factor
        words = np.array(list(sample_probability.keys()))
        probs = np.array(list(sample_probability.values()))
        while True:
            wrd_list = []
            sampled_index = np.random.multinomial(self.n_negs, probs)
            for index, count in enumerate(sampled_index):
                for _ in range(count):
                     wrd_list.append(words[index])
            yield wrd_list




