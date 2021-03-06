# -*- coding: utf-8 -*-
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

    def __init__(self, args, token, vocab, method, skip_subsampling=False):
        self.batch_size = args.batch_size
        self.window = args.window
        self.n_negs = args.n_negs
        self.vocab_size = len(vocab)
        self.idx_pad = vocab.idx_unk ### no need for additional token in vocab
        self.method = method
        self.corpus = []
        self.wrd2n = defaultdict(int)
        ntokens = 0
        nOOV = 0
        for file in args.data:
            f, is_gzip = open_file_read(file)
            for l in f:
                if is_gzip:
                    l = l.decode('utf8')
                toks = token.tokenize(l.strip(' \n'))
                idxs = []
                for tok in toks:
                    idx = vocab[tok]
                    if idx == vocab.idx_unk:
                        nOOV += 1
                    idxs.append(idx)
                    self.wrd2n[idx] += 1
                self.corpus.append(idxs)
                ntokens += len(idxs)
            f.close()
        pOOV = 100.0 * nOOV / ntokens
        logging.info('read {} sentences with {} tokens (%OOV={:.2f})'.format(len(self.corpus), ntokens, pOOV))
        ### subsample
        if not skip_subsampling:
            ntokens = self.SubSample(ntokens)
            logging.info('subsampled to {} tokens'.format(ntokens))


    def get_window_negs(self, toks, center, window, n_negs):
        wrd = toks[center]
        pos = []
        neg = []
        msk = [] #mask of positive words (to indicate true words 1.0 or padding 0.0)
        for i in range(center-window,center+window+1):
            if i < 0:
                pos.append(self.idx_pad)
                msk.append(False)
            elif i >= len(toks):
                pos.append(self.idx_pad)
                msk.append(False)
            elif i!=center:
                pos.append(toks[i])
                msk.append(True)
        n = 0
        while n < n_negs:
            idx = random.randint(1, self.vocab_size-1) #do not consider idx=0 (unk)
            if idx in pos or idx == wrd:
                continue
            neg.append(idx)
            n += 1
        return wrd, pos, neg, msk

    def get_sentence_negs(self, sentence, center, n_negs):
        wrd = sentence[center]
        snt = list(sentence)
        del snt[center]
        msk = [True] * len(snt)
        neg = []
        n = 0
        while n < n_negs:
            idx = random.randint(1, self.vocab_size-1) #do not consider idx=0 (unk)
            if idx in snt or idx == wrd:
                continue
            neg.append(idx)
            n += 1
        return wrd, snt, neg, msk

    def __iter__(self):
        ######################################################
        ### infer_sent #######################################
        ######################################################
        if self.method == 'infer_sent':
            length = [len(self.corpus[i]) for i in range(len(self.corpus))]
            indexs = np.argsort(np.array(length))
            batch_snt = []
            batch_len = []
            batch_ind = []
            for index in indexs:
                snt = self.corpus[index]
                batch_snt.append(snt)
                batch_len.append(len(snt))
                batch_ind.append(index)
                ### add padding
                if len(batch_snt) > 1 and len(snt) > len(batch_snt[0]): 
                    for k in range(len(batch_snt)-1):
                        addn = len(batch_snt[-1]) - len(batch_snt[k])
                        batch_snt[k] += [self.idx_pad]*addn
                ### batch filled
                if len(batch_snt) == self.batch_size:
                    yield [batch_snt, batch_len, batch_ind]
                    batch_snt = []
                    batch_len = []
                    batch_ind = []
            if len(batch_snt):
                yield [batch_snt, batch_len, batch_ind]

        ######################################################
        ### infer_word #######################################
        ######################################################
        elif self.method == 'infer_word':
            batch_wrd = []
            batch_isnt = []
            batch_iwrd = []
            for index in range(len(self.corpus)):
                for iwrd in range(len(self.corpus[index])):
                    batch_wrd.append(self.corpus[index][iwrd])
                    batch_isnt.append(index)
                    batch_iwrd.append(iwrd)
                    ### batch filled
                    if len(batch_wrd) == self.batch_size:
                        yield [batch_wrd,batch_isnt,batch_iwrd]
                        batch_wrd = []
                        batch_isnt = []
                        batch_iwrd = []
            if len(batch_wrd):
                yield [batch_wrd,batch_isnt,batch_iwrd]

        ######################################################
        ### skipgram / cbow ##################################
        ######################################################
        #center word will be embedded by Input
        #positive and negative words will be embedded by Output
        elif self.method == 'skipgram' or self.method == 'cbow':
            indexs = [i for i in range(len(self.corpus))]
            random.shuffle(indexs) 
            batch_wrd = []
            batch_pos = []
            batch_neg = []
            batch_msk = []
            for index in indexs:
                toks = self.corpus[index]
                if len(toks) < 2: ### may be subsampled
                    continue
                for i in range(len(toks)):
                    wrd, pos, neg, msk = self.get_window_negs(toks,i,self.window,self.n_negs)
                    batch_wrd.append(wrd)
                    batch_pos.append(pos)
                    batch_neg.append(neg)
                    batch_msk.append(msk)
                    if len(batch_wrd) == self.batch_size:
                        yield [batch_wrd, batch_pos, batch_neg, batch_msk]
                        batch_wrd = []
                        batch_pos = []
                        batch_neg = []
                        batch_msk = []
            if len(batch_wrd):
                yield [batch_wrd, batch_pos, batch_neg, batch_msk]

        ######################################################
        ### sbow #############################################
        ######################################################
        elif self.method == 'sbow':
            length = [len(self.corpus[i]) for i in range(len(self.corpus))]
            indexs = np.argsort(np.array(length)) ### from smaller to largest sentences
            batch_wrd = []
            batch_snt = []
            batch_neg = []
            batch_msk = []
            for index in indexs:
                toks = self.corpus[index]
                if len(toks) < 2: ### may be subsampled
                    continue
                for i in range(len(toks)): #for each word in toks. Ex: 'a monster lives in my head'
                    wrd, snt, neg, msk = self.get_sentence_negs(toks,i,self.n_negs)
                    batch_wrd.append(wrd)
                    batch_snt.append(snt)
                    batch_neg.append(neg)
                    batch_msk.append(msk)
                    ### add padding
                    if len(batch_snt) > 1 and len(snt) > len(batch_snt[0]): 
                        for k in range(len(batch_snt)-1):
                            addn = len(snt) - len(batch_snt[k])
                            batch_snt[k] += [self.idx_pad]*addn
                            batch_msk[k] += [False]*addn
                    ### batch filled
                    if len(batch_wrd) == self.batch_size:
                        yield [batch_wrd, batch_snt, batch_neg, batch_msk]
                        batch_wrd = []
                        batch_snt = []
                        batch_neg = []
                        batch_msk = []
            if len(batch_wrd):
                yield [batch_wrd, batch_snt, batch_neg, batch_msk]

        ######################################################
        ### error ############################################
        ######################################################
        else:
            logging.error('bad -method option {}'.format(self.method))
            sys.exit()


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




