import sys
import random
import logging
import argparse
from collections import defaultdict

def create_logger(logfile, loglevel):
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = getattr(logging, "INFO", None)
    if logfile is None or logfile == "stderr":
        logging.basicConfig(format="[%(asctime)s.%(msecs)03d] %(levelname)s %(message)s", datefmt="%Y-%m-%d_%H:%M:%S", level=numeric_level)
    else:
        logging.basicConfig(filename=logfile, format="[%(asctime)s.%(msecs)03d] %(levelname)s %(message)s", datefmt="%Y-%m-%d_%H:%M:%S", level=numeric_level)

def addGap(gap, args):
    options = [] #### contains all available gap pairs (first, last)
    for first in range(len(gap)):
        if gap[first]: ### already a gap
            continue
        if first>0 and gap[first-1]: ### next to a previous gap
            continue
        for last in range(first,min(len(gap),first+args.l)):
            if gap[last]: ### already a gap
                break
            if last < len(gap)-1 and gap[last+1]: ### previous to a next gap
                break
            options.append([first,last])
    logging.debug("otions: {}".format(options))
    ### insert a gap in gap among all available in options (return its length)
    n_so_far = gap.count(1)
    random.shuffle(options)
    for ntry in range(min(5,len(options))):
        first, last = options[ntry]
        l = last-first+1
        ratio = (n_so_far+l) / float(len(gap))
        if ratio > args.r:
            continue
        for i in range(first, last+1):
            gap[i] = 1
        logging.debug("option: {}".format(options[ntry]))
        logging.debug("GAP[{:.2f}]: {}".format(ratio,gap))
        return l
    return 0
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate synthetic data with gaps to fill from parallel sentences.')
    parser.add_argument('-k', type=int, default=5, help='Max number of gaps in a sentence (def 5)')
    parser.add_argument('-l', type=int, default=5, help='Max length (space-separated tokens) of a gap (def 5)')
    parser.add_argument('-r', type=float, default=0.5, help='Max ratio gap_words/total_words (def 0.5)')
    parser.add_argument('-gap', type=str, default="｟gap｠", help='Token used to mark a gap')
    parser.add_argument('-sep', type=str, default="｟sep｠", help='Token used to separate input stream')
    parser.add_argument('-seed', type=int, default=0, help='Seed for randomness (def 0: no seed)')
    parser.add_argument('-log', default='info', help="Logging [debug, info, warning, critical, error] (info)")
    args = parser.parse_args()
    create_logger('stderr',args.log)
    if args.seed:
        random.seed(args.seed)
            
    length_gaps = defaultdict(int)
    number_gaps = defaultdict(int)
    nout = 0
    nline = 0
    for line in sys.stdin:
        nline += 1
        source_target = line.rstrip("\n").split('\t')
        if len(source_target) != 2:
            logging.error('input must contain 2 fields (source and target)')
        src = source_target.pop(0)
        ref = source_target.pop(0)
        logging.debug("SRC: {}".format(src))
        logging.debug("REF: {}".format(ref))
        tok = ref.split()
        logging.debug("TOK: {}".format(tok))
        gap = [0] * len(tok) ### gap will be like: [0 0 1 1 0 1 0 0 0 1 1 1 0]
        num_gaps = 0
        for k in range(random.randint(1,args.k)): ### [1, max_gaps]
            l = addGap(gap, args)
            if l == 0:
                break
            num_gaps += 1
            length_gaps[l] += 1
        if num_gaps == 0:
            continue
        number_gaps[num_gaps] += 1
            
        tgt = []
        gaps = []
        for i in range(len(tok)):
            if gap[i]:
                if i==0 or not gap[i-1]: ### new gap
                    tgt.append(args.gap)
                    gaps.append(tok[i])
                else: ### gap continuation
                    gaps[-1] += " " + tok[i]
            else:
                tgt.append(tok[i])

        for i in range(len(gaps)): ### add gap token in the begining of every gap sequence
            gaps[i] = "{} ".format(args.gap) + gaps[i]

        logging.debug('TGT: {}'.format(tgt))
        logging.debug('GAP: {}'.format(gaps))
        print("{} {} {}\t{}".format(src, args.sep, ' '.join(tgt), ' '.join(gaps)))
        nout += 1
        
    logging.info("Found {} sentences".format(nline))
    total = 0
    for k,n in sorted(number_gaps.items()):
        total += n
        logging.info("sentences with {} gaps: {} [{:.2f}%] => {}".format(k,n,100.0*n/nout,total))
    total = 0
    for l,n in sorted(length_gaps.items()):
        total += l*n
        logging.info("gaps with length {}: {} => {}".format(l,n,total))
        
