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

def sequence_mask(lengths):
    lengths = np.array(lengths)
    bs = len(lengths)
    l = lengths.max()
    msk = np.cumsum(np.ones([bs,l],dtype=int), axis=1).T #[l,bs] (transpose to allow combine with lenghts)
    mask = (msk <= lengths) ### i use lenghts-1 because the last unpadded word is <eos> and i want it masked too
    return mask.T #[bs,l]

def create_logger(logfile, loglevel):
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        sys.stderr.write("Invalid log level={}\n".format(loglevel))
        sys.exit()
    if logfile is None or logfile == 'stderr':
        logging.basicConfig(format='[%(asctime)s.%(msecs)03d] %(levelname)s %(message)s', datefmt='%Y-%m-%d_%H:%M:%S', level=numeric_level)
        logging.info('Created Logger level={}'.format(loglevel))
    else:
        logging.basicConfig(filename=logfile, format='[%(asctime)s.%(msecs)03d] %(levelname)s %(message)s', datefmt='%Y-%m-%d_%H:%M:%S', level=numeric_level)
        logging.info('Created Logger level={} file={}'.format(loglevel, logfile))

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

def do_train(args):
    if not os.path.exists(args.name + '.token'):
        logging.error('missing {} file (run preprocess mode)'.format(args.name + '.token'))
        sys.exit()
    if not os.path.exists(args.name + '.vocab'):
        logging.error('missing {} file (run preprocess mode)'.format(args.name + '.vocab'))
        sys.exit()

    token = OpenNMTTokenizer(args.name + '.token')
    vocab = Vocab()
    vocab.read(args.name + '.vocab')
    model = Word2Vec(len(vocab), args.embedding_size, vocab.idx_unk)
    if args.cuda:
        model.cuda()
#    optimizer = torch.optim.Adam(model.parameters(), lr=args.learning_rate, betas=(args.beta1,args.beta2), eps=args.eps)
#    optimizer = torch.optim.SGD(model.parameters(), lr=0.05)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate, betas=(args.beta1, args.beta2), eps=args.eps, weight_decay=0.01, amsgrad=False)

    n_steps, model, optimizer = load_model_optim(args.name, args.embedding_size, vocab, model, optimizer)

    dataset = Dataset(args, token, vocab)
    dataset.build_batchs()
    n_epochs = 0
    losses = []
    while True:
        n_epochs += 1
        for batch in dataset:
            model.train()
            if args.method == 'sgram':
                loss = model.forward_sgram(batch)
            elif args.method == 'cbow':
                loss = model.forward_cbow(batch)
            elif args.method == 's2vec':
                loss = model.forward_s2vec(batch)
            else:
                logging.error('bad -method option {}'.format(args.method))
                sys.exit()
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            n_steps += 1
            losses.append(loss.data.cpu().detach().numpy())
            if n_steps % args.report_every_n_steps == 0:
                accum_loss = np.mean(losses)
                logging.info('{} n_epoch={} n_steps={} Loss={:.6f}'.format(args.method, n_epochs,n_steps,accum_loss))
                losses = []
            if n_steps % args.save_every_n_steps == 0:
                save_model_optim(args.name, model, optimizer, n_steps, args.keep_last_n)
        if n_epochs >= args.max_epochs:
            logging.info('Stop (max epochs reached)')
            break
    save_model_optim(args.name, model, optimizer, n_steps, args.keep_last_n)

def do_infer_word(args):
    if not os.path.exists(args.name + '.token'):
        logging.error('missing {} file (run preprocess mode)'.format(args.name + '.token'))
        sys.exit()
    if not os.path.exists(args.name + '.vocab'):
        logging.error('missing {} file (run preprocess mode)'.format(args.name + '.vocab'))
        sys.exit()
    if len(glob.glob(args.name + '.model.?????????.pth')) == 0:
        logging.error('no model available: {}'.format(args.name + '.model.?????????.pth'))
        sys.exit()

    token = OpenNMTTokenizer(args.name + '.token')
    vocab = Vocab()
    vocab.read(args.name + '.vocab')
    model = Word2Vec(len(vocab), args.embedding_size, vocab.idx_unk)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.learning_rate, betas=(args.beta1,args.beta2), eps=args.eps)
    n_steps, model, optimizer = load_model_optim(args.name, args.embedding_size, vocab, model, optimizer)
    if args.cuda:
        model.cuda()

    if args.sim == 'cos':
        distance = nn.CosineSimilarity(dim=1, eps=1e-6)
    elif args.sim == 'pairwise':
        distance = nn.PairwiseDistance(eps=1e-6)
    else:
        logging.error('bad -sim option {}'.format(args.sim))
        sys.exit()

    dataset = Dataset(args, token, vocab, skip_subsampling=True)
    dataset.build_batchs_infer_word()
    with torch.no_grad():
        model.eval()
        voc_i = [i for i in range(0,len(vocab))]
        voc_e = model.Embed(voc_i,'iEmb')
        for batch in dataset:
            #batch[0] batch_wrd
            #batch[1] batch_isnt
            #batch[2] batch_iwrd
            wrd_i = batch[0]
            wrd_e = model.Embed(wrd_i, 'iEmb') #.cpu().detach().numpy().tolist()

            for i in range(len(wrd_i)): ### words to find their closest
                ind_snt = batch[1][i]
                ind_wrd = batch[2][i]
                wrd = vocab[wrd_i[i]]
                out = []
                out.append("{}:{}:{}".format(ind_snt,ind_wrd,wrd))

                dist = distance(wrd_e[i].unsqueeze(0),voc_e)
                print('dist.shape',dist.shape)
                mininds = torch.argsort(dist,dim=0,descending=True)
                for k in range(1,len(mininds)):
                    ind = mininds[k].item() #cpu().detach().numpy()
                    if i != ind:
                        out.append("{:.6f}:{}".format(dist[i].item(),vocab[ind]))
                        if len(out)-1 == args.k:
                            break
                print('\t'.join(out))


def do_infer_sent(args):
    if not os.path.exists(args.name + '.token'):
        logging.error('missing {} file (run preprocess mode)'.format(args.name + '.token'))
        sys.exit()
    if not os.path.exists(args.name + '.vocab'):
        logging.error('missing {} file (run preprocess mode)'.format(args.name + '.vocab'))
        sys.exit()
    if len(glob.glob(args.name + '.model.?????????.pth')) == 0:
        logging.error('no model available: {}'.format(args.name + '.model.?????????.pth'))
        sys.exit()

    token = OpenNMTTokenizer(args.name + '.token')
    vocab = Vocab()
    vocab.read(args.name + '.vocab')
    model = Word2Vec(len(vocab), args.embedding_size, vocab.idx_unk)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.learning_rate, betas=(args.beta1,args.beta2), eps=args.eps)
    n_steps, model, optimizer = load_model_optim(args.name, args.embedding_size, vocab, model, optimizer)
    if args.cuda:
        model.cuda()

    dataset = Dataset(args, token, vocab, skip_subsampling=True)
    dataset.build_batchs_infer_sent()
    with torch.no_grad():
        model.eval()
        for batch in dataset:
            snts = model.SentEmbed(batch[0], batch[1], 'iEmb', args.pooling).cpu().detach().numpy().tolist()
            for i in range(len(snts)):
                sentence = ["{:.6f}".format(w) for w in snts[i]]
                print('{}\t{}'.format(batch[2][i]+1, ' '.join(sentence) ))


def do_preprocess(args):

    if args.tok_conf is None:
        opts = {}
        opts['mode'] = 'space'
        with open(args.name + '.token', 'w') as yamlfile:
            _ = yaml.dump(opts, yamlfile)
    else:
        with open(args.tok_conf) as yamlfile: 
            opts = yaml.load(yamlfile, Loader=yaml.FullLoader)
            #cp bpe args.name+'.bpe'
            #replace in opts the bpe path
            yaml.dump(opts, args.name + '.token')
    logging.info('built tokenizer config file')

    token = OpenNMTTokenizer(args.name + '.token')
    vocab = Vocab()
    vocab.build(args.data,token,min_freq=args.voc_minf,max_size=args.voc_maxs)
    vocab.dump(args.name + '.vocab')
    logging.info('built vocab')

################################################################
### args #######################################################
################################################################
class Args():

    def __init__(self, argv):
        self.name = None
        self.data = None
        self.mode = None
        self.seed = 12345
        self.cuda = False
        self.log_file = None
        self.log_level = 'debug'
        self.voc_minf = 5
        self.voc_maxs = 0
        self.tok_conf = None
        self.train = None
        self.method = 'sgram'
        self.pooling = 'avg'
        self.batch_size = 1024
        self.max_epochs = 100
        self.embedding_size = 100
        self.window = 5
        self.n_negs = 10
        self.learning_rate = 0.001
        self.eps = 1e-08
        self.beta1 = 0.9
        self.beta2 = 0.999
        self.skip_subsampling = False    
        self.keep_last_n = 5
        self.save_every_n_steps = 5000
        self.report_every_n_steps = 500
        self.k = 5
        self.sim = 'cos'
        self.prog = argv.pop(0)
        self.usage = '''usage: {} -name STRING -mode STRING -data FILES [Options]
   -name         STRING : experiment name
   -mode         STRING : train, infer_sent, infer_word, preprocess
   -data          FILES : comma-separated OR with scaped wildcards

 Options:
   -seed            INT : seed value                                (12345)
   -log_file       FILE : log file (use stderr for STDERR)          ([name].log)
   -log_level     LEVEL : debug, info, warning, critical, error     (debug) 
   -cuda                : use CUDA                                  (False)
   -h                   : this help
 -------- When preprocessing -------------------------------------------------
   -voc_minf        INT : min frequency to consider a word          (5)
   -voc_maxs        INT : max size of vocabulary (0 for unlimitted) (0)
   -tok_conf       FILE : YAML file with onmt tokenization options  (space)
 -------- When learning ------------------------------------------------------
   -method       STRING : sgram, cbow, dbow, s2vec                  (sgram)
   -pooling      STRING : max, avg                                  (avg)
   -embedding_size  INT : embedding dimension                       (100)
   -window          INT : window size for skip-gram algorithm       (5)
   -n_negs          INT : number of negative samples generated      (10)
   -skip_subsampling    : do not subsample corpora                  (False)
   -batch_size      INT : batch size used                           (1024)
   -max_epochs      INT : stop learning after this number of epochs (100)
   -learning_rate FLOAT : learning rate for Adam optimizer          (0.001)
   -eps           FLOAT : eps for Adam optimizer                    (1e-08)
   -beta1         FLOAT : beta1 for Adam optimizer                  (0.9)
   -beta2         FLOAT : beta2 for Adam optimizer                  (0.999)
   -keep_last       INT : keep last n checkpoints                   (5)
   -save_every      INT : save checkpoint every n learning steps    (5000)
   -report_every    INT : print report every n learning steps       (500)
 -------- When inference -----------------------------------------------------
   -k               INT : find k closest words to each word in file (5)
   -sim          STRING : cos, pairwise                             (cos)
   -pooling      STRING : max, avg                                  (avg)

*** The script needs:
  + pytorch:   conda install pytorch torchvision cudatoolkit=10.1 -c pytorch
  + pyyaml:    pip install PyYAML
  + pyonmttok: pip install pyonmttok
'''.format(self.prog)

        if len(argv) == 0:
            sys.stderr.write("{}".format(self.usage))
            sys.exit()

        while len(argv):
            tok = argv.pop(0)
            if   (tok=="-name" and len(argv)): self.name = argv.pop(0)
            elif (tok=="-mode" and len(argv)): self.mode = argv.pop(0)
            elif (tok=="-data" and len(argv)): self.data = argv.pop(0)
            elif (tok=="-cuda"): self.cuda = True
            elif (tok=="-seed" and len(argv)): self.seed = int(argv.pop(0))
            elif (tok=="-log_file" and len(argv)): self.log_file = argv.pop(0)
            elif (tok=="-log_level" and len(argv)): self.log_level = argv.pop(0)
            elif (tok=="-voc_minf" and len(argv)): self.voc_minf = int(argv.pop(0))
            elif (tok=="-voc_maxs" and len(argv)): self.voc_maxs = int(argv.pop(0))
            elif (tok=="-toc_conf" and len(argv)): self.toc_conf = argv.pop(0)
            elif (tok=="-batch_size" and len(argv)): self.batch_size = int(argv.pop(0))
            elif (tok=="-max_epochs" and len(argv)): self.max_epochs = int(argv.pop(0))
            elif (tok=="-embedding_size" and len(argv)): self.embedding_size = int(argv.pop(0))
            elif (tok=="-window" and len(argv)): self.window = int(argv.pop(0))
            elif (tok=="-n_negs" and len(argv)): self.n_negs = int(argv.pop(0))
            elif (tok=="-learning_rate" and len(argv)): self.learning_rate = float(argv.pop(0))
            elif (tok=="-eps" and len(argv)): self.eps = float(argv.pop(0))
            elif (tok=="-beta1" and len(argv)): self.beta1 = float(argv.pop(0))
            elif (tok=="-beta2" and len(argv)): self.beta2 = float(argv.pop(0))
            elif (tok=="-skip_subsampling"): self.skip_subsampling = True
            elif (tok=="-keep_last" and len(argv)): self.keep_last_n = int(argv.pop(0))
            elif (tok=="-save_every" and len(argv)): self.save_every_n_steps = int(argv.pop(0))
            elif (tok=="-report_every" and len(argv)): self.report_every_n_steps = int(argv.pop(0))
            elif (tok=="-k" and len(argv)): self.k = int(argv.pop(0))
            elif (tok=="-sim" and len(argv)): self.sim = argv.pop(0)
            elif (tok=="-method" and len(argv)): self.method = argv.pop(0)
            elif (tok=="-pooling" and len(argv)): self.pooling = argv.pop(0)
            elif (tok=="-h"):
                sys.stderr.write("{}".format(self.usage))
                sys.exit()
            else:
                sys.stderr.write('error: unparsed {} option\n'.format(tok))
                sys.stderr.write("{}".format(self.usage))
                sys.exit()

        if self.log_file is None:
            self.log_file = self.name + '.log'

        create_logger(self.log_file, self.log_level)

        if self.name is None:
            logging.error('missing -name option')
            sys.exit()

        if self.mode is None:
            logging.error('missing -mode option')
            sys.exit()

        if self.data is None:
            logging.error('missing -data option')
            sys.exit()

        if self.seed > 0:
            random.seed(self.seed)
            torch.manual_seed(self.seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(self.seed)
            logging.debug('random seed set to {}'.format(self.seed))

        if ',' in self.data:
            self.data = self.data.split(',')
        else:
            self.data = glob.glob(self.data)


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

    def forward_sgram(self, batch):
        min_ = 1e-06
        max_ = 1.0 - 1e-06
        #batch[0] : batch of words (list)
        #batch[1] : batch of context words (list of list)
        #batch[2] : batch of negative words (list of list)
        emb  = self.Embed(batch[0],'iEmb') #[bs,ds,1]
        cemb = self.Embed(batch[1],'oEmb') #[bs,2*window,ds]
        nemb = self.Embed(batch[2],'oEmb') #[bs,n_negs,ds]
        # the output layer generates probabilities for each vocabulary item (using a softmax)
        # in our case, probabilities are generated only for selected context/negative words
        # for which probabilities are simulated following the sigmoid
        # the negative logarithm of these probabilities (sigmoid) is then used as loss function

        # for context words, the probability should be 1.0, then
        # if prob=1.0 => neg(log(prob))=0.0
        # if prob=0.0 => neg(log(prob))=Inf
        out = torch.bmm(cemb, emb.unsqueeze(2)).squeeze() #[bs,2*window,ds] x [bs,ds,1] = [bs,2*window,1] => [bs,2*window]
        sigmoid = out.sigmoid().clamp(min_, max_)
        neg_log_sigmoid = sigmoid.log().neg()       #[bs,2*window]
        ploss = neg_log_sigmoid.mean(1) #[bs] mean loss predicting all positive words on each batch
        # for negative words, the probability should be 0.0, then
        # if prob=1.0 => neg(log(-prob+1))=Inf
        # if prob=0.0 => neg(log(-prob+1))=0.0
        out = torch.bmm(nemb, emb.unsqueeze(2)).squeeze()  #[bs,n_negs]
        sigmoid = (-out.sigmoid()+1.0).clamp(min_, max_)
        neg_log_sigmoid = sigmoid.log().neg() #[bs,2*window]
        nloss = neg_log_sigmoid.mean(1) #[bs] mean loss predicting all negative words on each batch

        loss = ploss.mean() + nloss.mean()
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
        emb  = self.Embed(batch[0],'oEmb') #[bs,ds]
        cemb = self.Embed(batch[1],'iEmb') #[bs,2*window,ds]
        nemb = self.Embed(batch[2],'oEmb') #[bs,n_negs,ds]
        cemb_mean = torch.mean(cemb, dim=1) #[bs,ds] #mean of context words
        # for context words, the probability should be 1.0, then
        # if prob=1.0 => neg(log(prob))=0.0
        # if prob=0.0 => neg(log(prob))=Inf
        out = torch.bmm(cemb_mean.unsqueeze(1), emb.unsqueeze(-1)).squeeze() #[bs,1,ds] x [bs,ds,1] = [bs,1,1] => [bs]
        sigmoid = out.sigmoid().clamp(min_, max_) #[bs]
        neg_log_sigmoid = sigmoid.log().neg() #[bs] 
        ploss = neg_log_sigmoid.mean() #[1] mean loss predicting batch positive words
        # for negative words, the probability should be 0.0, then
        # if prob=1.0 => neg(log(-prob+1))=Inf
        # if prob=0.0 => neg(log(-prob+1))=0.0
        out = torch.bmm(cemb_mean.unsqueeze(1), nemb.transpose(1,2)).squeeze(1) #[bs,1,ds] x [bs, ds, n_negs] = [bs,1,n_negs] => [bs,n_negs]
        sigmoid = (-out.sigmoid()+1.0).clamp(min_, max_) #[bs,n_negs]
        neg_log_sigmoid = sigmoid.log().neg() #[bs,n_negs]
        nloss = neg_log_sigmoid.mean(1) #[bs] for each batch, mean of the negative words loss

        loss = ploss + nloss.mean()
        if torch.isnan(loss).any() or torch.isinf(loss).any():
            logging.error('NaN/Inf detected in cbow_loss for batch {}'.format(batch))
            sys.exit()

        return loss

    def forward_s2vec(self, batch):
        min_ = 1e-06
        max_ = 1.0 - 1e-06
        #batch[0] : batch of words (list)
        #batch[1] : batch of context words (list of list)
        #batch[2] : batch of negative words (list of list)
        #batch[3] : batch of sentences (list of list)
        #batch[4] : batch of lengths (list)
        emb  = self.Embed(batch[0],'oEmb') #[bs,ds]
        nemb = self.Embed(batch[2],'oEmb') #[bs,n_negs,ds]
        semb = self.SentEmbed(batch[3], batch[4], 'iEmb', 'avg') #[bs,ds] #mean of sentences considering their lens
        # for sentence, the probability should be 1.0, then
        # if prob=1.0 => neg(log(prob))=0.0
        # if prob=0.0 => neg(log(prob))=Inf
        out = torch.bmm(semb.unsqueeze(1), emb.unsqueeze(-1)).squeeze() #[bs,1,ds] x [bs,ds,1] = [bs,1,1] => [bs]
        sigmoid = out.sigmoid().clamp(min_, max_) #[bs]
        neg_log_sigmoid = sigmoid.log().neg() #[bs] 
        ploss = neg_log_sigmoid.mean() #[1] mean loss predicting batch positive words
        # for negative words, the probability should be 0.0, then
        # if prob=1.0 => neg(log(-prob+1))=Inf
        # if prob=0.0 => neg(log(-prob+1))=0.0
        out = torch.bmm(emb.unsqueeze(1), nemb.transpose(1,2)).squeeze(1) #[bs,1,ds] x [bs, ds, n_negs] = [bs,1,n_negs] => [bs,n_negs]
        sigmoid = (-out.sigmoid()+1.0).clamp(min_, max_) #[bs,n_negs]
        neg_log_sigmoid = sigmoid.log().neg() #[bs,n_negs]
        nloss = neg_log_sigmoid.mean(1) #[bs] for each batch, mean of the negative words loss

        loss = ploss + nloss.mean()
        if torch.isnan(loss).any() or torch.isinf(loss).any():
            logging.error('NaN/Inf detected in s2vec_loss for batch {}'.format(batch))
            sys.exit()

        return loss

####################################################################
### Main ###########################################################
####################################################################
if __name__ == "__main__":

    args = Args(sys.argv) #creates logger and sets random seed

    if args.mode == 'preprocess':
        do_preprocess(args)

    elif args.mode == 'train':
        do_train(args)

    elif args.mode == 'infer_sent':
        do_infer_sent(args)

    elif args.mode == 'infer_word':
        do_infer_word(args)

    else:
        logging.error('bad -mode option {}'.format(args.mode))

    logging.info('Done!')


