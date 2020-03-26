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

min_sigm = 1e-06
max_sigm = 1.0 - 1e-06

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
    def __init__(self, vs, ds, pooling, pad_idx):
        super(Word2Vec, self).__init__()
        self.vs = vs
        self.ds = ds
        self.pooling = pooling
        self.pad_idx = pad_idx
        self.iEmb = nn.Embedding(self.vs, self.ds, padding_idx=self.pad_idx)#, max_norm=float(ds), norm_type=2)
        self.oEmb = nn.Embedding(self.vs, self.ds, padding_idx=self.pad_idx)#, max_norm=float(ds), norm_type=2)
        #nn.init.xavier_uniform_(self.iEmb.weight)
        #nn.init.xavier_uniform_(self.oEmb.weight)
        nn.init.uniform_(self.iEmb.weight, -0.1, 0.1)
        nn.init.uniform_(self.oEmb.weight, -0.1, 0.1)

    def SentEmbed(self, snt, lens, layer):
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
            logging.error('bad layer value {}'.format(self.pooling))
            sys.exit()

        mask = mask.unsqueeze(-1) #[bs, lw, 1]
        if self.pooling == 'max':
            #torch.max returns the maximum value of each row of the input tensor in the given dimension dim.
            #since masked tokens after iemb*mask are 0.0 we need to make sure that 0.0 is not the max
            #so all these masked tokens are added -999.9
            semb, _ = torch.max(semb*mask + (1.0-mask)*-999.9, dim=1) #-999.9 should be -Inf but it produces a nan when multiplied by 0.0            
        elif self.pooling == 'avg':
            semb = semb*mask
            semb = torch.sum(semb, dim=1)
            semb = semb / torch.sum(mask, dim=1) 
        elif self.pooling == 'sum':
            semb = semb*mask
            semb = torch.sum(semb, dim=1)
        else:
            logging.error('bad -pooling option {}'.format(self.pooling))
            sys.exit()
        if torch.isnan(semb).any():
            logging.error('nan detected in snt_iemb')
            sys.exit()
        return semb


    def Embed(self, wrd, layer, pooling):
        self.pooling = pooling
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
        #batch[0] : batch of center words (list)
        #batch[1] : batch of positive words (list of list)
        #batch[2] : batch of negative words (list of list)
        #batch[3] : batch of masks for positive words (list of list)
        msk = torch.as_tensor(batch[3]) #[bs,n] (positive words are 1.0 others are 0.0)
        if self.iEmb.weight.is_cuda:
            msk = msk.cuda()

        #Center word is embedded using iEmb
        wrd_emb = self.Embed(batch[0],'iEmb') #[bs,ds]
        #Positive/Negative words are embedded using oEmb
        pos_emb = self.Embed(batch[1],'oEmb') #[bs,n,ds]  
        neg_emb = self.Embed(batch[2],'oEmb').neg() #[bs,n,ds]  
        ###
        ### computing positive words loss
        ###
        #i use clamp to prevent NaN/Inf appear when computing the log of 1.0/0.0
        err = torch.bmm(wrd_emb.unsqueeze(1), pos_emb.transpose(2,1)).squeeze().sigmoid().clamp(min_sigm, max_sigm).log().neg() #[bs,1,ds] x [bs,ds,n] = [bs,1,n] = > [bs,n]
        err = torch.sum(err*msk, dim=1) / torch.sum(msk, dim=1) #[bs] (avg errors of positive words)
        loss = err.mean()
        ###
        ### computing negative words loss
        ###
        err = torch.bmm(wrd_emb.unsqueeze(1), neg_emb.transpose(2,1)).squeeze().sigmoid().clamp(min_sigm, max_sigm).log().neg() #[bs,1,ds] x [bs,ds,n] = [bs,1,n] = > [bs,n]
        err = torch.sum(err, dim=1) #[bs] (sum errors of negative words)
        #do not average errors over negative words
        loss += err.mean()

        if torch.isnan(loss).any() or torch.isinf(loss).any():
            logging.error('NaN/Inf detected in sgram_loss for batch {}'.format(batch))
            sys.exit()        
            
        return loss

    def forward_cbow(self, batch):
        #batch[0] : batch of center words (list)
        #batch[1] : batch of positive words (list of list)
        #batch[2] : batch of negative words (list of list)
        #batch[3] : batch of masks for positive words (list of list)
        msk = torch.as_tensor(batch[3]) #[bs,n] (positive words are 1.0 others are 0.0)
        if self.iEmb.weight.is_cuda:
            msk = msk.cuda()

        #Positive words are embedded using the iEmb
        pos_emb = self.Embed(batch[1],'iEmb') #[bs,n,ds]
        #positive embedding result from the average of all positive embeddings
        if self.pooling == 'avg':
            pos_emb = (pos_emb*msk.unsqueeze(-1)).sum(1) / torch.sum(msk, dim=1).unsqueeze(-1) #[bs,n,ds]x[bs,n,1]=>[bs,ds] / [bs,1] = [bs,ds] 
        elif self.pooling == 'sum':
            pos_emb = (pos_emb*msk.unsqueeze(-1)).sum(1) #[bs,n,ds]x[bs,n,1]=>[bs,ds] 
        elif self.pooling == 'max':
            pos_emb, _ = torch.max(pos_emb*msk + (1.0-msk)*-999.9, dim=1) #-999.9 should be -Inf but it produces a nan when multiplied by 0.0            
        else:
            logging.error('bad -pooling option {}'.format(self.pooling))
            sys.exit()

        #Center words are embedded using oEmb
        wrd_emb = self.Embed(batch[0],'oEmb') #[bs,ds]
        #Negative words are embedded using oEmb
        neg_emb = self.Embed(batch[2],'oEmb').neg() #[bs,n,ds]
        ###
        ### computing positive words loss
        ###
        #i use clamp to prevent NaN/Inf appear when computing the log of 1.0/0.0
        err = torch.bmm(pos_emb.unsqueeze(1), wrd_emb.unsqueeze(-1)).squeeze().sigmoid().clamp(min_sigm, max_sigm).log().neg() #[bs,1,ds] x [bs,ds,1] = [bs,1] = > [bs]
        loss = err.mean() # no need to average positive words errors since there is only one
        ###
        ### computing negative words loss
        ###
        err = torch.bmm(pos_emb.unsqueeze(1), neg_emb.transpose(2,1)).squeeze().sigmoid().clamp(min_sigm, max_sigm).log().neg() #[bs,1,ds] x [bs,ds,n] = [bs,1,n] = > [bs,n]
        err = torch.sum(err, dim=1) #[bs] (sum of errors of all negative words) (not averaged)
        loss += err.mean()

        if torch.isnan(loss).any() or torch.isinf(loss).any():
            logging.error('NaN/Inf detected in cbow_loss for batch {}'.format(batch))
            sys.exit()
        return loss

    def forward_sbow(self, batch):
        #batch[0] : batch of center words (list)
        #batch[1] : batch of sentences (list of list)
        #batch[2] : batch of negative words (list of list)
        #batch[3] : batch of sentence masks (list of list)
        msk = torch.as_tensor(batch[3]) #[bs,n] (positive words are 1.0 others are 0.0)
        if self.iEmb.weight.is_cuda:
            msk = msk.cuda()

        #Sentences are embedded using iEmb
        snt_emb = self.Embed(batch[1], 'iEmb') #[bs,n,ds]
        #sentence embedding result from the avg/sum/max of all its word embeddings
        if self.pooling == 'avg':
            snt_emb = (snt_emb*msk.unsqueeze(-1)).sum(1) / torch.sum(msk, dim=1).unsqueeze(-1) #[bs,n,ds]x[bs,n,1]=>[bs,ds] / [bs,1] = [bs,ds] 
        elif self.pooling == 'sum':
            snt_emb = (snt_emb*msk.unsqueeze(-1)).sum(1) #[bs,n,ds]x[bs,n,1]=>[bs,ds] 
        elif self.pooling == 'max':
            snt_emb, _ = torch.max(snt_emb*msk + (1.0-msk)*-999.9, dim=1) #-999.9 should be -Inf but it produces a nan when multiplied by 0.0            
        else:
            logging.error('bad -pooling option {}'.format(self.pooling))
            sys.exit()

        #Center words are embedded using oEmb
        wrd_emb  = self.Embed(batch[0],'oEmb') #[bs,ds]
        #Negative words are embedded using oEmb
        neg_emb = self.Embed(batch[2],'oEmb').neg() #[bs,n,ds]

        ###
        ### computing sentence words loss
        ###
        #i use clamp to prevent NaN/Inf appear when computing the log of 1.0/0.0
        err = torch.bmm(snt_emb.unsqueeze(1), wrd_emb.unsqueeze(-1)).squeeze().sigmoid().clamp(min_sigm, max_sigm).log().neg() #[bs,1,ds] x [bs,ds,1] = [bs,1] = > [bs]
        loss = err.mean() # no need to average positive words errors since there is only one
        ###
        ### computing negative words loss
        ###
        err = torch.bmm(snt_emb.unsqueeze(1), neg_emb.transpose(2,1)).squeeze().sigmoid().clamp(min_sigm, max_sigm).log().neg() #[bs,1,ds] x [bs,ds,n] = [bs,1,n] = > [bs,n]
        err = torch.sum(err, dim=1) #[bs] (sum of errors of all negative words) (not averaged)
        loss += err.mean()

        if torch.isnan(loss).any() or torch.isinf(loss).any():
            logging.error('NaN/Inf detected in sbow_loss for batch {}'.format(batch))
            sys.exit()

        return loss


