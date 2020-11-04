# -*- coding: utf-8 -*-

import io
import os
import sys
import logging
from multiprocessing import Process
from time import time

def create_logger(logfile, loglevel):
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        logging.error("Invalid log level={}".format(loglevel))
        sys.exit()
    if logfile is None or logfile == 'stderr':
        logging.basicConfig(format='[%(asctime)s.%(msecs)03d] %(levelname)s %(message)s', datefmt='%Y-%m-%d_%H:%M:%S', level=numeric_level)
        logging.debug('Created Logger level={}'.format(loglevel))
    else:
        logging.basicConfig(filename=logfile, format='[%(asctime)s.%(msecs)03d] %(levelname)s %(message)s', datefmt='%Y-%m-%d_%H:%M:%S', level=numeric_level)
        logging.debug('Created Logger level={} file={}'.format(loglevel, logfile))

######################################################################
### ARGS #############################################################
######################################################################

class Args():

  def __init__(self, argv):    
    self.s = None
    self.t = None
    self.a = None
    self.o = None
    self.l = '7'
    self.step = 1
    self.parallel = False
    
    self.lexscore = 'corpora-tools/corpus/lexical_score.perl'
    self.extract = '/TOOLS/3rdParty/linux/ubuntu-18.04/gcc-7.4.0/c++11/64/release-12/moses/4.0.16/bin/extract'
    self.score = '/TOOLS/3rdParty/linux/ubuntu-18.04/gcc-7.4.0/c++11/64/release-12/moses/4.0.16/bin/score'
    self.consolidate = '/TOOLS/3rdParty/linux/ubuntu-18.04/gcc-7.4.0/c++11/64/release-12/moses/4.0.16/bin/consolidate'
    self.sort = 'LC_ALL=C sort --compress-program=gzip --parallel=16 --temporary-directory=/tmp/big_files'

    log_file = None
    log_level = 'info'
    prog = argv.pop(0)
    usage = '''usage: {} -s FILE -t FILE -a FILE
  -s           FILE : tokenized source file
  -t           FILE : tokenized target file
  -a           FILE : source-to-target alignment file
  -o           FILE : output pattern file

  -step         INT : begin on this step   (1)
  -parallel         : run in parallel      (False) 

  -l            INT : max phrase length    (7)
  -lexscore    FILE : lexical scorer       (corpora-tools/corpus/lexical_score.perl)
  -extract     FILE : phrase extractor     (/TOOLS/3rdParty/linux/ubuntu-18.04/gcc-7.4.0/c++11/64/release-12/moses/4.0.16/bin/extract)
  -score       FILE : phrase scorer        (/TOOLS/3rdParty/linux/ubuntu-18.04/gcc-7.4.0/c++11/64/release-12/moses/4.0.16/bin/score)
  -consolidate FILE : phrase consolidation (/TOOLS/3rdParty/linux/ubuntu-18.04/gcc-7.4.0/c++11/64/release-12/moses/4.0.16/bin/consolidate)
  -sort     COMMAND : sorting command      (LC_ALL=C sort --compress-program=gzip --parallel=16 --temporary-directory=/tmp/big_files)

  -log_file    FILE : log file             (stderr)
  -log_level STRING : log level [debug, info, warning, critical, error] (info)
  -h                : this help

Steps:
 + 1:lexscore
 + 2:phrase extract
 + 3:phrase score
 + 4:consolidate
'''.format(prog)
    
    while len(sys.argv):
      tok = sys.argv.pop(0)
      if tok=="-h":
        sys.stderr.write("{}".format(usage))
        sys.exit()
      elif tok=="-parallel":
        self.parallel = True
      elif tok=="-s" and len(sys.argv):
        self.s = sys.argv.pop(0)
      elif tok=="-t" and len(sys.argv):
        self.t = sys.argv.pop(0)
      elif tok=="-a" and len(sys.argv):
        self.a = sys.argv.pop(0)
      elif tok=="-o" and len(sys.argv):
        self.o = sys.argv.pop(0)
      elif tok=="-l" and len(sys.argv):
        self.l = sys.argv.pop(0)
      elif tok=="-step" and len(sys.argv):
        self.step = int(sys.argv.pop(0))
      elif tok=="-lexscore" and len(sys.argv):
        self.lexscore = sys.argv.pop(0)
      elif tok=="-extract" and len(sys.argv):
        self.extract = sys.argv.pop(0)
      elif tok=="-score" and len(sys.argv):
        self.score = sys.argv.pop(0)
      elif tok=="-consolidate" and len(sys.argv):
        self.consolidate = sys.argv.pop(0)
      elif tok=="-sort" and len(sys.argv):
        self.sort = sys.argv.pop(0)
      elif tok=="-log_file" and len(sys.argv):
        log_file = sys.argv.pop(0)
      elif tok=="-log_level" and len(sys.argv):
        log_level = sys.argv.pop(0)
      else:
        sys.stderr.write('error: unparsed {} option\n'.format(tok))
        sys.stderr.write("{}".format(usage))
        sys.exit()

    create_logger(log_file,log_level)

    if self.s is None:
        logging.error('error: missing -s option')
        sys.stderr.write("{}".format(usage))
        sys.exit()

    if self.t is None:
        logging.error('error: missing -t option')
        sys.stderr.write("{}".format(usage))
        sys.exit()

    if self.a is None:
        logging.error('error: missing -a option')
        sys.stderr.write("{}".format(usage))
        sys.exit()

    if self.o is None:
        logging.error('error: missing -o option')
        sys.stderr.write("{}".format(usage))
        sys.exit()
        
    if self.step <= 1 and not os.path.isfile(self.lexscore):
        logging.error('{} does not exist'.format(self.lexscore))
        sys.exit()

    if self.step <= 2 and not os.path.isfile(self.extract):
        logging.error('{} does not exist'.format(self.extract))
        sys.exit()

    if self.step <= 3 and not os.path.isfile(self.score):
        logging.error('{} does not exist'.format(self.score))
        sys.exit()

    if self.step <= 4 and not os.path.isfile(self.consolidate):
        logging.error('{} does not exist'.format(self.consolidate))
        sys.exit()

    for key,val in vars(self).items():
        logging.debug("{}: {}".format(key,val))

##################################################################
### calls ########################################################
##################################################################

def run(cmd):
    logging.info('RUNNING: {}'.format(cmd))
    os.system(cmd)

def run_inv(args):
    if args.step <= 2:
        run('zcat {} | {} | gzip -c - > {}'.format(args.o+'.extract.inv.gz', args.sort, args.o+'.extract.inv.sorted.gz'))
    if args.step <= 3:
        run('{} {} {} {} 2> {}'.format(args.score, args.o+'.extract.inv.sorted.gz', args.o+'.lex-s2t', args.o+'.phrases.t2s.gz', args.o+'.log.phrases.t2s'))
        run('zcat {} | {} | gzip -c - > {}'.format(args.o+'.phrases.t2s.gz', args.sort, args.o+'.phrases.t2s.sorted.gz'))

def run_dir(args):
    if args.step <= 2:
        run('zcat {} | {} | gzip -c - > {}'.format(args.o+'.extract.gz', args.sort, args.o+'.extract.sorted.gz'))
    if args.step <= 3:
        run('{} {} {} {} 2> {}'.format(args.score, args.o+'.extract.sorted.gz', args.o+'.lex-t2s', args.o+'.phrases.s2t.gz', args.o+'.log.phrases.s2t'))

######################################################################
### MAIN #############################################################
######################################################################
            
if __name__ == '__main__':

    args = Args(sys.argv)

    if args.step <= 1:
        run('perl {} -s {} -t {} -a {} -o {} 2> {}'.format(args.lexscore, args.s, args.t, args.a, args.o, args.o+'.log.lex-s2t'))

    if args.step <= 2:
        run('{} {} {} {} {} {} {} 2> {}'.format(args.extract, args.t, args.s, args.a, args.o+'.extract', args.l, '--GZOutput', args.o+'.log.extract'))

    if args.parallel:
        logging.info('Parallel processing')
        p_dir = Process(target=run_dir(args))
        p_inv = Process(target=run_inv(args))
        #run both
        p_dir.start()
        p_inv.start()
        #wait
        p_dir.join()
        p_inv.join()
        logging.info('End Parallel processing')
    else:
        logging.info('Sequential processing')
        run_dir(args)
        run_inv(args)

    if args.step <= 4:
        run('{} {} {} {} 2> {}'.format(args.consolidate, args.o+'.phrases.s2t.gz', args.o+'.phrases.t2s.sorted.gz', args.o+'.phrases.gz', args.o+'.log.phrases'))

    logging.info('Done')











    