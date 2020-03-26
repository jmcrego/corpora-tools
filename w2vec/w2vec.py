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
from model import Word2Vec, load_model_optim, save_model_optim


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

def read_params(args):
    embedding_size = None
    if not os.path.exists(args.name + '.param'):
        logging.error('missing {}.param file'.format(args.name))
        sys.exit()

    with open(args.name + '.param', 'r') as f:
        for line in f:
            desc, val = line.rstrip().split(' ')
            if desc == 'embedding_size':
                embedding_size = int(val)
                logging.info('updated embedding_size {}'.format(embedding_size))
    if embedding_size is None:
        logging.error('missing embedding_size in {}.param'.format(args.name))
        sys.exit()
    return embedding_size

def write_params(args):
    with open(args.name + '.param', 'w') as f:
        f.write('embedding_size {}\n'.format(args.embedding_size))

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
    if os.path.exists(args.name + '.param'):
        args.embedding_size = read_params(args)
    else:
        write_params(args)        

    model = Word2Vec(len(vocab), args.embedding_size, args.pooling, vocab.idx_unk)
    if args.cuda:
        model.cuda()
#    optimizer = torch.optim.Adam(model.parameters(), lr=args.learning_rate, betas=(args.beta1,args.beta2), eps=args.eps)
#    optimizer = torch.optim.SGD(model.parameters(), lr=0.05)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate, betas=(args.beta1, args.beta2), eps=args.eps, weight_decay=0.01, amsgrad=False)
    n_steps, model, optimizer = load_model_optim(args.name, args.embedding_size, vocab, model, optimizer)
    dataset = Dataset(args, token, vocab, args.method)

    n_epochs = 0
    losses = []
    while True:
        n_epochs += 1
        for batch in dataset:
            model.train()
            if args.method == 'skipgram':
                loss = model.forward_skipgram(batch)
            elif args.method == 'cbow':
                loss = model.forward_cbow(batch)
            elif args.method == 'sbow':
                loss = model.forward_sbow(batch)
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
    args.embedding_size = read_params(args)
    model = Word2Vec(len(vocab), args.embedding_size, args.pooling, vocab.idx_unk)
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

    dataset = Dataset(args, token, vocab, 'infer_word', skip_subsampling=True)
    with torch.no_grad():
        model.eval()
        voc_i = [i for i in range(0,len(vocab))]
        voc_e = model.Embed(voc_i,'iEmb', args.pooling)
        for batch in dataset:
            #batch[0] batch_wrd
            #batch[1] batch_isnt
            #batch[2] batch_iwrd
            wrd_i = batch[0]
            wrd_e = model.Embed(wrd_i, 'iEmb', args.pooling) #.cpu().detach().numpy().tolist()

            for i in range(len(wrd_i)): ### words to find their closest
                ind_snt = batch[1][i]
                ind_wrd = batch[2][i]
                wrd = vocab[wrd_i[i]]
                out = []
                out.append("{}:{}:{}".format(ind_snt,ind_wrd,wrd))

                dist_wrd_voc = distance(wrd_e[i].unsqueeze(0),voc_e)
                mininds = torch.argsort(dist_wrd_voc,dim=0,descending=True)
                for k in range(1,len(mininds)):
                    ind = mininds[k].item() #cpu().detach().numpy()
                    if i != ind:
                        dis = dist_wrd_voc[ind].item()
                        wrd = vocab[ind]
                        out.append("{:.6f}:{}".format(dis,wrd))
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
    args.embedding_size = read_params(args)
    model = Word2Vec(len(vocab), args.embedding_size, args.pooling, vocab.idx_unk)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.learning_rate, betas=(args.beta1,args.beta2), eps=args.eps)
    n_steps, model, optimizer = load_model_optim(args.name, args.embedding_size, vocab, model, optimizer)
    if args.cuda:
        model.cuda()

    dataset = Dataset(args, token, vocab, 'infer_sent', skip_subsampling=True)
    with torch.no_grad():
        model.eval()
        for batch in dataset:
            snts = model.SentEmbed(batch[0], batch[1], 'iEmb').cpu().detach().numpy().tolist()
            for i in range(len(snts)):
                sentence = ["{:.6f}".format(w) for w in snts[i]]
                print('{}\t{}'.format(batch[2][i]+1, ' '.join(sentence) ))


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
        self.method = 'cbow'
        self.pooling = 'avg'
        self.batch_size = 2048
        self.max_epochs = 1
        self.embedding_size = 300
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
   -mode         STRING : preprocess, train, infer_sent, infer_word
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
   -method       STRING : skipgram, cbow, sbow                      (cbow)
   -pooling      STRING : max, avg, sum                             (avg)
   -embedding_size  INT : embedding dimension                       (300)
   -window          INT : window size                               (5)
   -n_negs          INT : number of negative samples generated      (10)
   -skip_subsampling    : do not subsample corpora                  (False)
   -batch_size      INT : batch size used                           (1024)
   -max_epochs      INT : stop learning after this number of epochs (1)
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
   -pooling      STRING : max, avg, sum                             (avg)

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


