#import sys
import copy
#import codecs
#import opennmt
import logging
#import argparse
#import pyonmttok
#import numpy as np
#import edit_distance
import tensorflow as tf

class onmt_align():
    def __init__(self, tokenizer, model, temperature):
        self.tokenizer = tokenizer
        self.model = model
        self.temperature = temperature
        logging.debug("onmt_align initialized")

    def tokenize(self, raw_batch): ### list of strings (raw)
        raw_batch = [s.strip() for s in raw_batch]
        logging.debug("RAW: {}".format(raw_batch))
        tok_batch, _ = self.tokenizer.tokenize_batch(raw_batch)
        logging.debug("TOK: {}".format(tok_batch))
        return tok_batch
        
    def encode(self, tok):
        ### tok is a list of lists of strings (list of tokens)
        tok_joined = [" ".join(t) for t in tok] ### list of sentences(strings) rather than list of list of tokens(strings)
        features = self.model.features_inputter.make_features(tok_joined)
        ids = features['ids'] #[n_sents, maxl]
        logging.debug("IDS: {}".format(ids))
        lengths = features["length"]
        logging.debug("lengths: {}".format(lengths))
        embeddings = self.model.features_inputter(features)
        logging.debug("EMB.shape={}".format(embeddings.shape))
        out, _, _ = self.model.encoder(embeddings, sequence_length=lengths) #[2*n, maxl, ed]
        logging.debug("OUT.shape={}".format(out.shape))
        return ids, lengths, out
       
    def align(self, out, ids): ### list of strings
        n = out.shape[0] // 2 #n sents par language
        maxl = out.shape[1]
        ed = out.shape[2]
        out_norm = tf.nn.l2_normalize(out,epsilon=1e-6,axis=2) #[2*n,maxl,ed]
        out_norm_src = out_norm[:n] #[n,maxl,ed]
        out_norm_tgt = out_norm[n:] #[n,maxl,ed]
        sim = tf.matmul(out_norm_src,out_norm_tgt,transpose_b=True) #[n,maxl,ed] x [n,ed,maxl] = [n,maxl(src),maxl(tgt)]
        sim = (sim + 1.0) / 2.0 #ranges [0,+1] instead of [-1,+1]
        ### set to 0.0 those values in matrix for which ids_src or ids_tgt are 0 (pad)
        ids_src = tf.expand_dims(tf.convert_to_tensor(ids[:n]), axis=2) #[n,maxl,1]
        ids_tgt = tf.expand_dims(tf.convert_to_tensor(ids[n:]), axis=1) #[n,1,maxl]
        msk = tf.matmul(ids_src,ids_tgt) #[n,maxl,maxl]
        msk = msk == 0 #true: words to be padded, false: rest
        sim = tf.where(msk, 0.0, sim) ### sim cells are: 0.0 if true in msk, original sim cell otherwise
        if self.temperature > 0:
            sim = sim/self.temperature #softmax with temperature
        sim = tf.nn.softmax(sim, axis=1) #[n,maxl,maxl] softmax (axis=1 softmax over src-side words, axis=2: softmax over tgt-side words)
        logging.debug("sim.shape={}".format(sim.shape))
        return sim

    def print_matrix(self,sim,att,lsrc,ltgt,rsrc,inp):
        logging.debug("input: {}".format([' '.join(inp)]))
        assert(len(lsrc) == sim.shape[0])
        assert(len(ltgt) == sim.shape[1])
        assert(len(ltgt) == att.shape[0])
        assert(len(lsrc) == rsrc.shape[0])
        lsrc = copy.deepcopy(lsrc)
        ltgt = copy.deepcopy(ltgt)
        ### lsrc contain rsrc
        lsrc = ["{}:{}".format(rsrc[s],lsrc[s]) for s in range(len(lsrc))]
        ### all tokens with maxc chars
        maxc = max([len(s) for s in lsrc] + [len('ATTENTION')] + [len(t) for t in ltgt]) + 1
        for i in range(len(lsrc)):
            lsrc[i] += " " * (maxc - len(lsrc[i]))
        for i in range(len(ltgt)):
            ltgt[i] += " " * (maxc - len(ltgt[i]))
        ### print matrix
        logging.debug(''.join([" "*maxc] + ltgt))
        for s in range(len(lsrc)):
            lsrc_s = [lsrc[s]] + ["{:.2f}".format(sim[s,t])+" "*(maxc-4) for t in range(sim.shape[1])]
            logging.debug(''.join(lsrc_s))
        att = ["{:.2f}".format(a)+" "*(maxc-4) for a in att]
        logging.debug('ATTENTION'+''.join([" "*(maxc-9)] + att))
        return

