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
        #batch[1] : batch of context words (list of list)
        #batch[2] : batch of positive words (list of list)
        #batch[3] : batch of negative words (list of list)
        pos = torch.as_tensor(batch[2]) #[bs,n] (positive words are 1.0 others are 0.0)
        neg = torch.as_tensor(batch[3]) #[bs,n] (negative words are 1.0 others are 0.0)
        if self.iEmb.weight.is_cuda:
            pos = pos.cuda()
            neg = neg.cuda()


        #Center word is embedded using the input embeddings (iEmb)
        wrd_emb = self.Embed(batch[0],'iEmb').unsqueeze(1) #[bs,ds] => [bs,1,ds]
        #Context words are embedded using the output embeddings (oEmb)
        ctx_emb = self.Embed(batch[1],'oEmb') #[bs,n,ds]  
        ctx_emb = (ctx_emb * (-2.0*neg.unsqueeze(-1) + 1.0)) #[bs,n,ds] (negative words are polarity inversed: multiplied by -1.0 rest are not impacted)

        ### errors are computed word by word using the neg(log(sigmoid(wrd*ctx)))
        #i use clamp to prevent NaN/Inf appear when computing the log of 1.0/0.0
        err = torch.bmm(wrd_emb, ctx_emb.transpose(2,1)).squeeze().sigmoid().clamp(min_, max_).log().neg() #[bs,1,ds] x [bs,ds,n] = [bs,1,n] = > [bs,n]

        ###
        ### computing positive words loss
        ###
        pos_err = torch.sum(err*pos, dim=1) #/ torch.sum(pos, dim=1) #[bs] (sum errors of positive words)
        avg_pos = True
        if avg_pos:
            pos_err = pos_err / torch.sum(pos, dim=1) #[bs] errors of positive words are averaged
        loss = pos_err.mean()
#        logging.info('ploss={:.5f}'.format(pos_loss_per_batch.mean().data.cpu().detach().numpy()))

        ###
        ### computing negative words loss
        ###
        neg_err = torch.sum(err*neg, dim=1) #[bs] (sum of errors of all negative words in each batch)
        avg_neg = False
        if avg_neg:
            neg_err = neg_err / torch.sum(neg, dim=1) #[bs] errors of negative words are averaged
        loss += neg_err.mean()
#        logging.info('nloss={:.5f}'.format(neg_err.mean().data.cpu().detach().numpy()))

        if torch.isnan(loss).any() or torch.isinf(loss).any():
            logging.error('NaN/Inf detected in sgram_loss for batch {}'.format(batch))
            sys.exit()        
            
        return loss

    def forward_cbow(self, batch):
        min_ = 1e-06
        max_ = 1.0 - 1e-06
        #batch[0] : batch of center words (list)
        #batch[1] : batch of context words (list of list)
        #batch[2] : batch of positive words (list of list)
        #batch[3] : batch of negative words (list of list)
        pos = torch.as_tensor(batch[2]) #[bs,n] (positive words are 1.0 others are 0.0)
        neg = torch.as_tensor(batch[3]) #[bs,n] (negative words are 1.0 others are 0.0)
        if self.iEmb.weight.is_cuda:
            pos = pos.cuda()
            neg = neg.cuda()

        #Center words are embedded using the output embeddings (oEmb)        
        wrd_emb = self.Embed(batch[0],'oEmb').unsqueeze(1) #[bs,ds] => [bs,1,ds]
        #Context words are embedded using the input embeddings (iEmb)
        ctx_emb = self.Embed(batch[1],'iEmb') #[bs,n,ds]
#        ctx_emb = ctx_emb * (-2.0*neg.unsqueeze(-1) + 1.0) #[bs,n,ds] (negative words are polarity inversed: multiplied by -1.0 rest are not impacted)
        #all positive word embeddings are averaged into a single vector representing positive context words [bs,ds]
        pos_emb = (ctx_emb*pos.unsqueeze(-1)).sum(1) #/ torch.sum(pos, dim=1).unsqueeze(-1) #[bs,n,ds]x[bs,n,1]=>[bs,ds] / [bs,1] = [bs,ds] 

        ###
        ### computing positive words loss
        ###
        #i use clamp to prevent NaN/Inf appear when computing the log of 1.0/0.0
        pos_err = torch.bmm(wrd_emb, pos_emb.unsqueeze(-1)).squeeze().sigmoid().clamp(min_, max_).log().neg() #[bs,1,ds] x [bs,ds,1] = [bs,1] = > [bs]
        ### no need to average positive words errors since there is only one
        loss = pos_err.mean()
#        logging.info('ploss={:.5f}'.format(err.mean().data.cpu().detach().numpy()))

        ###
        ### computing negative words loss
        ###
        err = torch.bmm(wrd_emb, ctx_emb.transpose(2,1)).squeeze().sigmoid().clamp(min_, max_).log().neg() #[bs,1,ds] x [bs,ds,n] = [bs,1,n] = > [bs,n]
        neg_err = torch.sum(err*neg, dim=1) #[bs] (sum of errors of all negative words)
        avg_neg = False
        if avg_neg:
            neg_err = neg_err / torch.sum(neg, dim=1) #[bs] errors of negative words are averaged
        loss += neg_err.mean()
#        logging.info('nloss={:.5f}'.format(neg_loss_per_batch.mean().data.cpu().detach().numpy()))

        if torch.isnan(loss).any() or torch.isinf(loss).any():
            logging.error('NaN/Inf detected in cbow_loss for batch {}'.format(batch))
            sys.exit()
        return loss

    def forward_sbow(self, batch):
        min_ = 1e-06
        max_ = 1.0 - 1e-06
        #batch[0] : batch of words (list of list with one element)
        #batch[1] : batch of sentences (list of list)
        #batch[2] : batch of lengths (list)
        #batch[3] : batch of negative words (list of list)
        snt_emb = self.SentEmbed(batch[1], batch[2], 'iEmb', 'avg') #[bs,ds] #mean of sentences considering their lens

        wrd_emb  = self.Embed(batch[0],'oEmb').squeeze() #[bs,ds]
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


