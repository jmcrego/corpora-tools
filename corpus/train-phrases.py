# -*- coding: utf-8 -*-

import io
import sys
#import gzip
import logging
#import os
import os.path
import subprocess
from time import time

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
    self.steps = ['1','2','3','4']
    
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

  -l            INT : max phrase length    (7)
  -steps        INT : comma-separated list (1,2,3,4)
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
      elif tok=="-steps" and len(sys.argv):
        self.steps = sys.argv.pop(0).split(',')
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
        
    for key,val in vars(self).items():
        logging.info("{}: {}".format(key,val))

##################################################################
### calls ########################################################
##################################################################

def do_call(cmd):
    logging.info('RUNNING: {}'.format(cmd))
    os.system(cmd)

def do_calls(cmds):
    fd_s = []
    p_s = []
    for i in range(len(cmds)):
        ferr = cmds[i].pop()
        fd = open(ferr, "w")
        logging.info('RUNNING: {} 2> ferr'.format(cmds[i]))
        p = subprocess.Popen(cmds[i], stderr=fd)
        p_s.append(p)
        fd_s.append(fd)

    for i in range(len(p_s)):
        p_s[i].wait()

    for i in range(len(fd_s)):
        fd_s[i].close()


##################################################################
### steps ########################################################
##################################################################

def run_lexscore(args):
    logging.info('<<<<<<<<<< Step 1:lexscore >>>>>>>>>>>>>>>>>>>>>>>')
    if not os.path.isfile(args.lexscore):
        logging.error('{} does not exist'.format(args.lexscore))
        sys.exit()
    tic = time()
    do_call('perl {} -s {} -t {} -a {} -o {} 2> {}'.format(args.lexscore, args.s, args.t, args.a, args.o, args.o+'.log.lex-s2t'))
    #cmd = 'perl {} -s {} -t {} -a {} -o {} 2> {}'.format(args.lexscore, args.s, args.t, args.a, args.o, args.o+'.log.lex-s2t')
    #logging.info('RUNNING: {}'.format(cmd))
    #os.system(cmd)    
    toc = time()
    logging.info("lexscore took {:.2f} seconds".format(toc-tic))

def run_extract(args):
    logging.info('<<<<<<<<<< Step 2:extract >>>>>>>>>>>>>>>>>>>>>>>>')
    if not os.path.isfile(args.extract):
        logging.error('{} does not exist'.format(args.extract))
        sys.exit()

    tic = time()
    cmd = [args.extract, args.t, args.s, args.a, args.o+'.extract', args.l, '--GZOutput', args.o+'.log.extract']
    do_calls([cmd])
    #cmd = [args.extract, args.t, args.s, args.a, args.o+'.extract', args.l, '--GZOutput']
    #logging.info('RUNNING: {}'.format(' '.join(cmd)))
    #ferr=open(args.o+'.log.extract', "w")
    #p = subprocess.Popen(cmd, stderr=ferr)
    #p.wait()
    #ferr.close()

    do_call('zcat {} | {} | gzip -c - > {}'.format(args.o+'.extract.gz', args.sort, args.o+'.extract.sorted.gz'))
    #cmd = 'zcat {} | {} | gzip -c - > {}'.format(args.o+'.extract.gz', args.sort, args.o+'.extract.sorted.gz')
    #logging.info('RUNNING: {}'.format(cmd))
    #os.system(cmd)
    do_call('zcat {} | {} | gzip -c - > {}'.format(args.o+'.extract.inv.gz', args.sort, args.o+'.extract.inv.sorted.gz'))
    #cmd = 'zcat {} | {} | gzip -c - > {}'.format(args.o+'.extract.inv.gz', args.sort, args.o+'.extract.inv.sorted.gz')
    #logging.info('RUNNING: {}'.format(cmd))
    #os.system(cmd)
    toc = time()
    logging.info("extract took {:.2f} seconds".format(toc-tic))

def run_score(args):
    logging.info('<<<<<<<<<< Step 3:score >>>>>>>>>>>>>>>>>>>>>>>>>>')
    if not os.path.isfile(args.score):
        logging.error('{} does not exist'.format(args.score))
        sys.exit()

    tic = time()
    cmd1 = [args.score, args.o+'.extract.sorted.gz', args.o+'.lex-t2s', args.o+'.phrases.s2t.gz', args.o+'.log.phrases.s2t']
    cmd2 = [args.score, args.o+'.extract.inv.sorted.gz', args.o+'.lex-s2t', args.o+'.phrases.t2s.gz', '--Inverse', args.o+'.log.phrases.t2s']
    do_calls([cmd1, cmd2])

    #cmd1 = [args.score, args.o+'.extract.sorted.gz', args.o+'.lex-t2s', args.o+'.phrases.s2t.gz']
    #logging.info('RUNNING: {}'.format(' '.join(cmd1)))
    #ferr1=open(args.o+'.log.phrases.s2t', "w")
    #p1 = subprocess.Popen(cmd1, stderr=ferr1)

    #cmd2 = [args.score, args.o+'.extract.inv.sorted.gz', args.o+'.lex-s2t', args.o+'.phrases.t2s.gz', '--Inverse']
    #logging.info('RUNNING: {}'.format(' '.join(cmd2)))
    #ferr2=open(args.o+'.log.phrases.t2s', "w")
    #p2 = subprocess.Popen(cmd2, stderr=ferr2)

    #p1.wait()
    #p2.wait()  
    #ferr1.close()
    #ferr2.close()  

    do_call('zcat {} | {} | gzip -c - > {}'.format(args.o+'.phrases.t2s.gz', args.sort, args.o+'.phrases.t2s.sorted.gz'))
    #cmd = 'zcat {} | {} | gzip -c - > {}'.format(args.o+'.phrases.t2s.gz', args.sort, args.o+'.phrases.t2s.sorted.gz')
    #logging.info('RUNNING: {}'.format(cmd))
    #os.system(cmd)    
    toc = time()
    logging.info("score took {:.2f} seconds".format(toc-tic))

    
def run_consolidate(args):
    logging.info('<<<<<<<<<< Step 4:consolidate >>>>>>>>>>>>>>>>>>>>')
    if not os.path.isfile(args.consolidate):
        logging.error('{} does not exist'.format(args.consolidate))
        sys.exit()

    tic = time()
    do_call('{} {} {} {} 2> {}'.format(args.consolidate, args.o+'.phrases.s2t.gz', args.o+'.phrases.t2s.sorted.gz', args.o+'.phrases.gz', args.o+'.log.phrases'))
    #cmd = '{} {} {} {} 2> {}'.format(args.consolidate, args.o+'.phrases.s2t.gz', args.o+'.phrases.t2s.sorted.gz', args.o+'.phrases.gz', args.o+'.log.phrases')
    #logging.info('RUNNING: {}'.format(cmd))
    #os.system(cmd)    
    toc = time()
    logging.info("consolidate took {:.2f} seconds".format(toc-tic))

######################################################################
### MAIN #############################################################
######################################################################
            
if __name__ == '__main__':

    args = Args(sys.argv)
    if '1' in args.steps:
        run_lexscore(args)
    if '2' in args.steps:
        run_extract(args)
    if '3' in args.steps:
        run_score(args)
    if '4' in args.steps:
        run_consolidate(args)
    logging.info('Done')


    
