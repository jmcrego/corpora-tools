# -*- coding: utf-8 -*-
import sys
import numpy as np
import random
import logging
from collections import defaultdict

def create_logger(logfile, loglevel):
  numeric_level = getattr(logging, loglevel.upper(), None)
  if not isinstance(numeric_level, int):
    logging.error("Invalid log level={}".format(loglevel))
    sys.exit()
  if logfile is None or logfile == 'stderr':
    logging.basicConfig(format='[%(asctime)s.%(msecs)03d] %(levelname)s %(message)s', datefmt='%Y-%m-%d_%H:%M:%S', level=numeric_level)
    logging.info('Created Logger level={}'.format(loglevel))
  else:
    logging.basicConfig(filename=logfile, format='[%(asctime)s.%(msecs)03d] %(levelname)s %(message)s', datefmt='%Y-%m-%d_%H:%M:%S', level=numeric_level)
    logging.info('Created Logger level={} file={}'.format(loglevel, logfile))

def read_file(f):
  with open(f,"r") as fd: 
    vec = [l.strip() for l in fd.readlines()]
  logging.info('Read {} with {} entries'.format(f,len(vec)))
  return vec

######################################################################
### ARGS #############################################################
######################################################################

class Args():

  def __init__(self, argv):    
    self.fdb_src = None
    self.fdb_tgt = None
    self.fq_match = None
    self.fq_src = None
    self.fq_tgt = None
    self.cur = '⸨cur⸩'
    self.sep = '⸨sep⸩'
    self.range = False
    self.maxn = 1
    self.mins = 0.5
    self.perfect = 0.0
    self.inference = False
    self.verbose = False

    seed = 12345
    log_file = None
    log_level = 'info'
    prog = argv.pop(0)
    usage = '''usage: {} -db_src FILE -db_tgt FILE -q_src FILE -q_tgt FILE -q_match FILE
  -db_src    FILE : db file with src strings
  -db_tgt    FILE : db file with tgt strings
  -q_src     FILE : query file with src strings
  -q_tgt     FILE : query file with tgt strings
  -q_match   FILE : query file with matchs

  -mins       FLOAT : min similarity score                              (0.5)
  -maxn         INT : inject up to n-best context sentences             (1)
  -perfect    FLOAT : probability of injecting perfect matchs           (0.0) <not implemented>
  -sep       STRING : context sentence first token                      (⸨sep⸩)
  -cur       STRING : current sentence first token                      (⸨cur⸩)
  -range            : use score ranges to separate similar sentences    (False)
  -inference        : output a single example for all sentences         (False)

  -log_file    FILE : log file                                          (stderr)
  -log_level STRING : log level [debug, info, warning, critical, error] (info)
  -seed       FLOAT : seed for randomness                               (1234)
  -h                : this help
'''.format(prog)
    
    while len(sys.argv):
      tok = sys.argv.pop(0)
      if tok=="-h":
        sys.stderr.write("{}".format(usage))
        sys.exit()
      elif tok=="-db_src" and len(sys.argv):
        self.fdb_src = sys.argv.pop(0)
      elif tok=="-db_tgt" and len(sys.argv):
        self.fdb_tgt = sys.argv.pop(0)
      elif tok=="-q_src" and len(sys.argv):
        self.fq_src = sys.argv.pop(0)
      elif tok=="-q_tgt" and len(sys.argv):
        self.fq_tgt = sys.argv.pop(0)
      elif tok=="-q_match" and len(sys.argv):
        self.fq_match = sys.argv.pop(0)
      elif tok=="-maxn" and len(sys.argv):
        self.maxn = int(sys.argv.pop(0))
      elif tok=="-mins" and len(sys.argv):
        self.mins = float(sys.argv.pop(0))
      elif tok=="-sep" and len(sys.argv):
        self.sep = sys.argv.pop(0)
      elif tok=="-cur" and len(sys.argv):
        self.cur = sys.argv.pop(0)
      elif tok=="-perfect" and len(sys.argv):
        self.perfect = float(sys.argv.pop(0))
      elif tok=="-inference":
        self.inference = True
      elif tok=="-range":
        self.range = True
      elif tok=="-v":
        self.verbose = True
      elif tok=="-seed" and len(sys.argv):
        seed = int(sys.argv.pop(0))
      elif tok=="-log_file" and len(sys.argv):
        log_file = sys.argv.pop(0)
      elif tok=="-log_level" and len(sys.argv):
        log_level = sys.argv.pop(0)
      else:
        sys.stderr.write('error: unparsed {} option\n'.format(tok))
        sys.stderr.write("{}".format(usage))
        sys.exit()

    random.seed(seed)
    create_logger(log_file,log_level)

    if self.fdb_src is None:
        logging.error('error: missing -db_src option')
        sys.stderr.write("{}".format(usage))
        sys.exit()

    if self.fdb_tgt is None:
        logging.error('error: missing -db_tgt option')
        sys.stderr.write("{}".format(usage))
        sys.exit()

    if self.fq_src is None:
        logging.error('error: missing -q_src option')
        sys.stderr.write("{}".format(usage))
        sys.exit()

    if self.fq_tgt is None:
        logging.error('error: missing -q_tgt option')
        sys.stderr.write("{}".format(usage))
        sys.exit()

######################################################################
### get_contexts #####################################################
######################################################################

def get_contexts(match, args, db_src, db_tgt):
  contexts_src = []
  contexts_tgt = []
  contexts_scores = []
  if match=="":
    return contexts_src, contexts_tgt, contexts_scores 

  matches = match.split("\t")
  for m in range(len(matches)):
    if m%2 != 0:
      continue
    score = min(float(matches[m]), 1.0)
    id_db = int(matches[m+1])-1
    if score < args.mins:
      continue
    tag = "⸨" + "{:.1f}".format(score) + "⸩" if args.range else args.sep
    context_tgt = tag + " " + db_tgt[id_db]
    context_src = tag + " " + db_src[id_db]

    if context_tgt not in contexts_tgt and context_src not in contexts_src: ### not repeated pairs
      contexts_scores.append(score)
      contexts_tgt.append(context_tgt)
      contexts_src.append(context_src)

  if args.verbose:
    logging.info(contexts_scores)
    logging.info(contexts_src)
    logging.info(contexts_tgt)
  return contexts_src, contexts_tgt, contexts_scores 

######################################################################
### MAIN #############################################################
######################################################################

ctx2n = defaultdict(int)
tag2n = defaultdict(int)
slen2n = defaultdict(int)
tlen2n = defaultdict(int)

if __name__ == '__main__':

  args = Args(sys.argv)
  for key,val in vars(args).items():
    logging.info("{}: {}".format(key,val))

  db_src = read_file(args.fdb_src)
  db_tgt = read_file(args.fdb_tgt)
  q_match = read_file(args.fq_match)
  q_src = read_file(args.fq_src) if args.fdb_src != args.fq_src else db_src
  q_tgt = read_file(args.fq_tgt) if args.fdb_tgt != args.fq_tgt else db_tgt

  ext = ".mins{}.maxn{}".format(args.mins,args.maxn)
  if args.range:
    ext += ".range"
  if args.inference:
    ext += ".inference"

  fq_osrc_prime = open(args.fq_src + ext + '.prime' ,"w");
  fq_osrc_augm  = open(args.fq_src + ext + '.augm' ,"w");
  fq_otgt_pref  = open(args.fq_tgt + ext + '.pref',"w");
  fq_otgt_prime = open(args.fq_tgt + ext + '.prime',"w");
  fq_otgt_augm  = open(args.fq_tgt + ext + '.augm',"w");

  for i,(src,tgt,match) in enumerate(zip(q_src,q_tgt,q_match)):
    contexts_src, contexts_tgt, contexts_scores = get_contexts(match, args, db_src, db_tgt)
    ############################################
    ### no context, print original sentences ###
    ############################################
    if len(contexts_src) == 0 and len(contexts_tgt) == 0:
      print(src, file=fq_osrc_prime)
      print(src, file=fq_osrc_augm)
      print("",  file=fq_otgt_pref)
      print(tgt, file=fq_otgt_prime)
      print(tgt, file=fq_otgt_augm)
      ctx2n[0] += 1
      slen2n[len(src.split())] += 1
      tlen2n[len(tgt.split())] += 1
      continue
    ############################################
    ### context, print primed sentences ########
    ############################################
    contexts_inds = np.argsort(contexts_scores)[::-1] #sort in descending order
    prefix_src = []
    prefix_tgt = []
    count = 0
    count_src = 0
    count_tgt = 0
    for k,ind in enumerate(contexts_inds):
      if count_src<=100 and count_tgt<=100 and count<args.maxn:
        tag2n[contexts_src[ind].split()[0]] += 1
        prefix_src.insert(0,contexts_src[ind])
        prefix_tgt.insert(0,contexts_tgt[ind])
        count +=1
        count_src += len(contexts_src[ind])
        count_tgt += len(contexts_tgt[ind])
      else:
        print(" ".join(prefix_src) + " {} ".format(args.cur) + src, file=fq_osrc_prime)
        print(" ".join(prefix_tgt) + " {} ".format(args.cur) + src, file=fq_osrc_augm)
        print(" ".join(prefix_tgt) + " {} ".format(args.cur),       file=fq_otgt_pref)
        print(" ".join(prefix_tgt) + " {} ".format(args.cur) + tgt, file=fq_otgt_prime)
        print("{} ".format(args.cur) + tgt, file=fq_otgt_augm)
        ctx2n[count] += 1
        slen2n[len(prefix_src)+1+len(src.split())] += 1
        tlen2n[len(prefix_tgt)+1+len(tgt.split())] += 1
        prefix_src = []
        prefix_tgt = []
        count = 0
        count_src = 0
        count_tgt = 0
        if args.inference: ### if inference print one single example
          break
    if len(prefix_src) and len(prefix_tgt):
      print(" ".join(prefix_src) + " {} ".format(args.cur) + src, file=fq_osrc_prime)
      print(" ".join(prefix_tgt) + " {} ".format(args.cur) + src, file=fq_osrc_augm)
      print(" ".join(prefix_tgt) + " {} ".format(args.cur),       file=fq_otgt_pref)
      print(" ".join(prefix_tgt) + " {} ".format(args.cur) + tgt, file=fq_otgt_prime)
      print("{} ".format(args.cur) + tgt, file=fq_otgt_augm)
      ctx2n[count] += 1
      slen2n[len(prefix_src)+1+len(src.split())] += 1
      tlen2n[len(prefix_tgt)+1+len(tgt.split())] += 1

  fq_osrc_prime.close()
  fq_osrc_augm.close()
  fq_otgt_pref.close()
  fq_otgt_prime.close()
  fq_otgt_augm.close()

  nexamples = 0
  for n, N in sorted(ctx2n.items()):
    logging.info('{}-contexts => {}'.format(n,N))
    nexamples += N
  logging.info('Examples => {}'.format(nexamples))
  for n, N in sorted(tag2n.items()):
    logging.info('tag-{} => {}'.format(n,N))
  for n, N in sorted(slen2n.items()):
    logging.debug('slen:{} => {}'.format(n,N))
  for n, N in sorted(tlen2n.items()):
    logging.debug('tlen:{} => {}'.format(n,N))



