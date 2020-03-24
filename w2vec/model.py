# -*- coding: utf-8 -*-
import torch
import logging
import yaml
import sys
import os
import io
import math
import random
import itertools
import pyonmttok
import glob
import numpy as np
import torch.nn as nn
from collections import Counter
from dataset import Dataset, Vocab, OpenNMTTokenizer, open_file_read

def load_model_optim(pattern, EMBEDDING_SIZE, vocab, model, optimizer):
    files = sorted(glob.glob(pattern + '.model.?????????.pth')) 
    if len(files):
        file = files[-1] ### last is the newest
        checkpoint = torch.load(file)
        n_steps = checkpoint['n_steps']
        optimizer.load_state_dict(checkpoint['optimizer'])
        model.load_state_dict(checkpoint['model'])
        logging.info('loaded checkpoint {} [{},{}]'.format(file,len(vocab),EMBEDDING_SIZE))
    else:
        n_steps = 0
        logging.info('built model from scratch [{},{}]'.format(len(vocab),EMBEDDING_SIZE))
    return n_steps, model, optimizer

def save_model_optim(pattern, model, optimizer, n_steps, keep_last_n):
    file = pattern + '.model.{:09d}.pth'.format(n_steps)
    state = {
        'n_steps': n_steps,
        'optimizer': optimizer.state_dict(),
        'model': model.state_dict()
    }
    torch.save(state, file)
    logging.info('saved checkpoint {}'.format(file))
    files = sorted(glob.glob(pattern + '.model.?????????.pth')) 
    while len(files) > keep_last_n:
        f = files.pop(0)
        os.remove(f) ### first is the oldest
        logging.debug('removed checkpoint {}'.format(f))

def sequence_mask(lengths):
    lengths = np.array(lengths)
    bs = len(lengths)
    l = lengths.max()
    msk = np.cumsum(np.ones([bs,l],dtype=int), axis=1).T #[l,bs] (transpose to allow combine with lenghts)
    mask = (msk <= lengths) ### i use lenghts-1 because the last unpadded word is <eos> and i want it masked too
    return mask.T #[bs,l]


####################################################################
### Word2Vec #######################################################
####################################################################
class Word2Vec(nn.Module):
    def __init__(self, vs, ds, pad_idx):
        super(Word2Vec, self).__init__()
        self.vs = vs
        self.ds = ds
        self.pad_idx = pad_idx
        self.iEmb = nn.Embedding(self.vs, self.ds, padding_idx=self.pad_idx)#, max_norm=float(ds), norm_type=2)
        self.oEmb = nn.Embedding(self.vs, self.ds, padding_idx=self.pad_idx)#, max_norm=float(ds), norm_type=2)
        #nn.init.xavier_uniform_(self.iEmb.weight)
        #nn.init.xavier_uniform_(self.oEmb.weight)
        nn.init.uniform_(self.iEmb.weight, -0.1, 0.1)
        nn.init.uniform_(self.oEmb.weight, -0.1, 0.1)

    def SentEmbed(self, snt, lens, layer, pooling):
        #snt [bs, lw] batch of sentences (list of list of words)
        #lns [bs] length of each sentence in batch
        #mask [bs, lw] contains 0.0 for masked words, 1.0 for unmaksed ones
#        print('lens',lens)
        snt = torch.as_tensor(snt) ### [bs,lw] batch with sentence words
#        print('snt.shape',snt.shape)
        mask = torch.as_tensor(sequence_mask(lens))
#        print('mask.shape',mask.shape)
        if self.iEmb.weight.is_cuda:
            snt = snt.cuda()
            mask = mask.cuda()

        if layer == 'iEmb':
            semb = self.iEmb(snt)       
        elif layer == 'oEmb':
            semb = self.oEmb(snt)       
        else:
            logging.error('bad layer value {}'.format(pooling))
            sys.exit()

#        print('semb.shape',semb.shape)


        mask = mask.unsqueeze(-1) #[bs, lw, 1]
        if pooling == 'max':
            #torch.max returns the maximum value of each row of the input tensor in the given dimension dim.
            #since masked tokens after iemb*mask are 0.0 we need to make sure that 0.0 is not the max
            #so all these masked tokens are added -999.9
            semb, _ = torch.max(semb*mask + (1.0-mask)*-999.9, dim=1) #-999.9 should be -Inf but it produces a nan when multiplied by 0.0            
        elif pooling == 'avg':
            semb = semb*mask
#            print('semb2.shape',semb.shape)
            semb = torch.sum(semb, dim=1)
#            print('semb3.shape',semb.shape)
            semb = semb / torch.sum(mask, dim=1) 
#            print('semb4.shape',semb.shape)
#            sys.exit()
        else:
            logging.error('bad -pooling option {}'.format(pooling))
            sys.exit()
        if torch.isnan(semb).any():
            logging.error('nan detected in snt_iemb')
            sys.exit()
        return semb


    def NaN(self, wrd, emb):
        if len(wrd.shape) == 1:
            for i in range(len(wrd)):
                if torch.isnan(emb[i]).any() or torch.isinf(emb[i]).any():
                    logging.error('NaN/Inf detected\nwrd {}\nemb {}'.format(wrd[i],emb[i]))
        else:
            for i in range(len(wrd)):
                self.NaN(wrd[i],emb[i])

    def Embed(self, wrd, layer):
        wrd = torch.as_tensor(wrd) 
        if self.iEmb.weight.is_cuda:
            wrd = wrd.cuda()
        if torch.isnan(wrd).any() or torch.isinf(wrd).any():
            logging.error('NaN/Inf detected in input wrd {}'.format(wrd))
            sys.exit()            
        if layer == 'iEmb':
            emb = self.iEmb(wrd) #[bs,ds]
        elif layer == 'oEmb':
            emb = self.oEmb(wrd) #[bs,ds]
        else:
            logging.error('bad layer {}'.format(layer))
            sys.exit()
        if torch.isnan(emb).any() or torch.isinf(emb).any():
            logging.error('NaN/Inf detected in {} layer emb.shape={}\nwrds {}'.format(layer,emb.shape,wrd))
            self.NaN(wrd,emb)
            sys.exit()
        return emb

    def forward_skipgram(self, batch):
        min_ = 1e-06
        max_ = 1.0 - 1e-06
        #batch[0] : batch of center words (list)
        #batch[1] : batch of context words (list)
        #batch[2] : batch of n_sample negative words (list of list)

        #Center word is embedded using the input embeddings (iEmb)
        wrd_emb = self.Embed(batch[0],'iEmb') #[bs,ds]

        #Context words are embedded using the output embeddings (oEmb)
        ctx_emb = self.Embed(batch[1],'oEmb') #[bs,ds]
        # for context words, the probability should be 1.0, then
        # if prob=1.0 => neg(log(prob))=0.0
        # if prob=0.0 => neg(log(prob))=Inf
        out = torch.bmm(wrd_emb.unsqueeze(1), ctx_emb.unsqueeze(-1)).squeeze() #[bs,1,ds] x [bs,ds,1] = [bs,1,1] = > [bs]
        neg_log_sigmoid = out.sigmoid().clamp(min_, max_).log().neg() #[bs]
        ploss = neg_log_sigmoid.mean() #[1] batches mean loss

        #Negative words are embedded using the output embeddings (oEmb)
        neg_emb = self.Embed(batch[2],'oEmb').neg() #[bs,n_negs,ds]
        # for negative words, the probability should be 0.0, then
        # if prob=1.0 => neg(log(-prob+1))=Inf
        # if prob=0.0 => neg(log(-prob+1))=0.0
        out = torch.bmm(wrd_emb.unsqueeze(1), neg_emb.transpose(2,1)).squeeze()  #[bs,1,ds] x [bs,ds,n_negs] = [bs,1,n_negs] => [bs,n_negs]
        neg_log_sigmoid = out.sigmoid().clamp(min_, max_).log().neg() #[bs,n_negs]
        nloss = neg_log_sigmoid.sum(1) #[bs] sum of losses predicting all negative words on each batch
        nloss = nloss.mean() #[1] batches mean loss

        loss = ploss + nloss
        if torch.isnan(loss).any() or torch.isinf(loss).any():
            logging.error('NaN/Inf detected in sgram_loss for batch {}'.format(batch))
            sys.exit()        
            
        return loss

    def forward_cbow(self, batch):
        min_ = 1e-06
        max_ = 1.0 - 1e-06
        #batch[0] : batch of words (list)
        #batch[1] : batch of context words (list of list)
        #batch[2] : batch of negative words (list of list)

        #Context words are embedded using the input embeddings (iEmb)
        #the 2xwindow embeddings [bs,2*window,ds] are summed up into a single vector representing context words [bs,ds]
        ctx_emb = self.Embed(batch[1],'iEmb').sum(1) #[bs,2*window,ds] => [bs,ds] #sum of h's of the corresponding (2*window) context words

        #the center word is embedded using the output embeddings (oEmb)        
        # p(wrd|ctx) the probability of the input word given the context words should be 1.0, then
        wrd_emb  = self.Embed(batch[0],'oEmb') #[bs,ds]
        # if prob=1.0 => neg(log(prob))=0.0
        # if prob=0.0 => neg(log(prob))=Inf
        out = torch.bmm(ctx_emb.unsqueeze(1), wrd_emb.unsqueeze(-1)).squeeze() #[bs,1,ds] x [bs,ds,1] = [bs,1,1] => [bs]
        neg_log_sigmoid = out.sigmoid().clamp(min_, max_).log().neg() #[bs]
        ploss = neg_log_sigmoid.mean() #[1] batches mean loss


        #the n_negs negative words are embedded using the output embeddings (oEmb)
        # p(neg|ctx) for each negative word, the probability should be 0.0, then
        neg_emb = self.Embed(batch[2],'oEmb').neg() #[bs,n_negs,ds]
        # if prob=1.0 => neg(log(-prob+1))=Inf
        # if prob=0.0 => neg(log(-prob+1))=0.0
        out = torch.bmm(ctx_emb.unsqueeze(1), neg_emb.transpose(1,2)).squeeze(1) #[bs,1,ds] x [bs, ds, n_negs] = [bs,1,n_negs] => [bs,n_negs]
        neg_log_sigmoid = out.sigmoid().clamp(min_, max_).log().neg() #[bs,n_negs]
        nloss = neg_log_sigmoid.sum(1) #[bs] for each batch, sum of the n_negs negative words loss
        nloss = nloss.mean() #batches mean loss

        loss = ploss + nloss
        if torch.isnan(loss).any() or torch.isinf(loss).any():
            logging.error('NaN/Inf detected in cbow_loss for batch {}'.format(batch))
            sys.exit()

        return loss

    def forward_sbow(self, batch):
        min_ = 1e-06
        max_ = 1.0 - 1e-06
        #batch[0] : batch of words (list)
        #batch[1] : batch of sentences (list of list)
        #batch[2] : batch of lengths (list)
        #batch[3] : batch of negative words (list of list)
        snt_emb = self.SentEmbed(batch[1], batch[2], 'iEmb', 'avg') #[bs,ds] #mean of sentences considering their lens

        wrd_emb  = self.Embed(batch[0],'oEmb') #[bs,ds]
        #p(wrd|snt)
        out = torch.bmm(snt_emb.unsqueeze(1), wrd_emb.unsqueeze(-1)).squeeze() #[bs,1,ds] x [bs,ds,1] = [bs,1,1] => [bs]
        neg_log_sigmoid = out.sigmoid().clamp(min_, max_).log().neg() #[bs]
        ploss = neg_log_sigmoid.mean() #[1] batches mean loss

        #p(neg|snt)
        neg_emb = self.Embed(batch[3],'oEmb').neg() #[bs,n_negs,ds]
        #p(neg|snt)
        # for negative words, the probability should be 0.0, then
        # if prob=1.0 => neg(log(-prob+1))=Inf
        # if prob=0.0 => neg(log(-prob+1))=0.0
        out = torch.bmm(snt_emb.unsqueeze(1), neg_emb.transpose(1,2)).squeeze(1) #[bs,1,ds] x [bs, ds, n_negs] = [bs,1,n_negs] => [bs,n_negs]
        neg_log_sigmoid = out.sigmoid().clamp(min_, max_).log().neg() #[bs,n_negs]
        nloss = neg_log_sigmoid.sum(1) #[bs] for each batch, mean of the negative words loss
        nloss = nloss.mean()

        loss = ploss + nloss
        if torch.isnan(loss).any() or torch.isinf(loss).any():
            logging.error('NaN/Inf detected in sbow_loss for batch {}'.format(batch))
            sys.exit()

        return loss


