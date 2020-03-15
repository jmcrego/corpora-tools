
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
    optimizer = torch.optim.Adam(model.parameters(), lr=args.learning_rate, betas=(args.beta1,args.beta2), eps=args.eps)
    n_steps, model, optimizer = load_model_optim(args.name, args.embedding_size, vocab, model, optimizer)
    if args.cuda:
        model.cuda()

    dataset = Dataset(args, token, vocab)
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

def do_test(args):
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

    with torch.no_grad():
        model.eval()
        voc_i = [i for i in range(0,len(vocab))]
        voc_e = model.Embed(voc_i,'iEmb')
        for file in args.data:
            f, is_gzip = open_file_read(file)
            for l in f:
                if is_gzip:
                    l = l.decode('utf8')
                toks = token.tokenize(l.strip(' \n'))
                for wrd in toks:
                    i = vocab[wrd]
                    wrd_i = [i] * len(vocab)
                    wrd_e = model.Embed(wrd_i,'iEmb')

                    dist = distance(wrd_e,voc_e)
                    mininds = torch.argsort(dist,dim=0,descending=True)
                    out = []
                    out.append(wrd)
                    for j in range(1,len(mininds)):
                        ind = mininds[j].item() #cpu().detach().numpy()
                        if ind != i:
                            out.append("{:.5f}:{}".format(dist[ind].item(),vocab[ind]))
                            if len(out)-1 == args.k:
                                break
                    print('\t'.join(out))
            f.close()

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
   -mode         STRING : train, test, preprocess
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

    def forward_snt_iemb(self, snt, mask, pooling):
        #isnt [bs, lw] batch of sentences (list of list of words)
        #mask [bs, lw] contains 0.0 for masked words, 1.0 for unmaksed ones
        snt = torch.as_tensor(snt) ### [bs,lw] batch with sentence words
        if self.iEmb.weight.is_cuda:
            snt = snt.cuda()
        emb = self.iEmb(snt) #[bs,lw,ds]
        if pooling == 'max':
            #torch.max returns the maximum value of each row of the input tensor in the given dimension dim.
            #since masked tokens after iemb*mask are 0.0 we need to make sure that 0.0 is not the max
            #so all these masked tokens are added -999.9
            semb, _ = torch.max(emb*mask + (1.0-mask)*-999.9, dim=1) #-999.9 should be -Inf but it produces a nan when multiplied by 0.0            
        elif pooling == 'avg':
            semb = torch.sum(emb*mask, dim=1) / torch.sum(mask, dim=1) 
        else:
            logging.error('bad -pooling option {}'.format(pooling))
        if torch.isnan(semb).any():
            logging.error('nan detected in snt_iemb')
            sys.exit()
        return semb

    def Embed(self, wrd, layer):
        wrd = torch.as_tensor(wrd) 
        if self.iEmb.weight.is_cuda:
            wrd = wrd.cuda()
        if torch.isnan(wrd).any():
            logging.error('nan detected in inut wrds {}'.format(wrd))
            sys.exit()            
        if layer == 'iEmb':
            emb = self.iEmb(wrd) #[bs,ds]
        elif layer == 'oEmb':
            emb = self.oEmb(wrd) #[bs,ds]
        else:
            logging.error('bad layer {}'.format(layer))
            sys.exit()
        if torch.isnan(emb).any():
            logging.error('nan detected in {} layer\n{}'.format(layer,emb))
            for b in range(len(wrd)):
                if len(range wrd[b].shape)>1:
                    for i in range(len(wrd[b])):
                        if len(wrd[b][i].shape)>1:
                            for j in range(len(wrd[b])):
                                if torch.isnan(wrd[b][i][j]):
                                    logging.error('wrd {} emb {}'.format(wrd[b][i][j],emb[b][i][j]))
                        elif torch.isnan(emb[b][i].any()):
                            logging.error('wrd {} emb {}'.format(wrd[b][i],emb[b][i]))
                elif torch.isnan(emb[b].any()):
                    logging.error('wrd {} emb {}'.format(wrd[b],emb[b]))
            sys.exit()
        return emb

    def forward_sgram(self, batch):
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
        neg_log_sigmoid = out.sigmoid().log().neg()       #[bs,2*window]
        ploss = neg_log_sigmoid.mean(1)                   #[bs] loss mean predicting all positive words
        # for negative words, the probability should be 0.0, then
        # if prob=1.0 => neg(log(-prob+1))=Inf
        # if prob=0.0 => neg(log(-prob+1))=0.0
        out = torch.bmm(nemb, emb.unsqueeze(2)).squeeze()  #[bs,n_negs]
        neg_log_sigmoid = (-out.sigmoid()+1.0).log().neg() #[bs,2*window]
        nloss = neg_log_sigmoid.mean(1)                    #[bs] loss mean predicting all negative words

        loss = ploss.mean() + nloss.mean()
        if torch.isnan(loss):
            logging.error('nan detected in sgram_loss')
            sys.exit()        
            
        return loss

    def forward_cbow(self, batch):
        #batch[0] : batch of words (list)
        #batch[1] : batch of context words (list of list)
        #batch[2] : batch of negative words (list of list)
        emb  = self.Embed(batch[0],'oEmb') #[bs,ds,1]
        cemb = self.Embed(batch[1],'iEmb') #[bs,2*window,ds]
        nemb = self.Embed(batch[2],'iEmb') #[bs,n_negs,ds]
        cemb_mean = torch.mean(cemb, dim=1) #[bs,ds] #mean of context words
        nemb_mean = torch.mean(nemb, dim=1) #[bs,ds] #mean of negative words
        # for context words, the probability should be 1.0, then
        # if prob=1.0 => neg(log(prob))=0.0
        # if prob=0.0 => neg(log(prob))=Inf
        out = torch.bmm(cemb_mean.unsqueeze(1), emb.unsqueeze(-1)).squeeze() #[bs,1,ds] x [bs,ds,1] = [bs,1,1] => [bs]
        neg_log_sigmoid = out.sigmoid().log().neg() #[bs] 
        ploss = neg_log_sigmoid.mean() #[bs]
        # for negative words, the probability should be 0.0, then
        # if prob=1.0 => neg(log(-prob+1))=Inf
        # if prob=0.0 => neg(log(-prob+1))=0.0
        out = torch.bmm(nemb_mean.unsqueeze(1), emb.unsqueeze(-1)).squeeze() #[bs]
        neg_log_sigmoid = (-out.sigmoid()+1.0).log().neg() #[bs]
        nloss = neg_log_sigmoid.mean() #[bs]

        loss = ploss + nloss
        if torch.isnan(loss):
            logging.error('nan detected in cbow_loss')
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

    elif args.mode == 'test':
        do_test(args)

    else:
        logging.error('bad -mode option {}'.format(args.mode))

    logging.info('Done!')


