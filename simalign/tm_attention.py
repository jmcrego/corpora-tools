import sys
import opennmt
import logging
import argparse
import pyonmttok
import tensorflow as tf
from onmt_align import onmt_align
from related import related

def create_logger(logfile, loglevel):
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = getattr(logging, "INFO", None)
    if logfile is None or logfile == "stderr":
        logging.basicConfig(format="[%(asctime)s.%(msecs)03d] %(levelname)s %(message)s", datefmt="%Y-%m-%d_%H:%M:%S", level=numeric_level)
    else:
        logging.basicConfig(filename=logfile, format="[%(asctime)s.%(msecs)03d] %(levelname)s %(message)s", datefmt="%Y-%m-%d_%H:%M:%S", level=numeric_level)

def batch(linp, lref, lsrc, ltgt, s, args):
    assert(len(lsrc) == len(lref))
    assert(len(lsrc) == len(ltgt))
    assert(len(lsrc) == len(linp))
    n = len(lsrc)
    tok = s.tokenize(linp + lref + lsrc + ltgt) #all lists with same size (<pad> when needed)
    ids,lengths,out = s.encode(tok[2*n:]) #only src and tgt are encoded (not inp nor ref)
    sim = s.align(out,ids) #[n,maxl,maxl]
    for i in range(n):
        nsrc = lengths[i]
        assert(nsrc > 0)
        ntgt = lengths[n+i]
        assert(ntgt > 0)
        curr_sim = sim[i,:nsrc,:ntgt]
        curr_inp = tok[0*n+i]
        curr_ref = tok[1*n+i]
        curr_src = tok[2*n+i]
        curr_tgt = tok[3*n+i]
        assert nsrc == len(curr_src), "{} != {}\t{}".format(nsrc, len(curr_src), curr_src)
        rsrc = related(curr_src, curr_inp).first()
        rsrc = tf.expand_dims(tf.convert_to_tensor(rsrc,dtype=tf.float32), axis=0) #[1,nsrc]
        curr_att = tf.squeeze(tf.linalg.matmul(rsrc,curr_sim),axis=0) #[1,nsrc] x [nsrc,ntgt] = [1,ntgt] = [ntgt]
        if args.log == 'debug':
            s.print_matrix(curr_sim,curr_att,curr_src,curr_tgt,rsrc[0],curr_inp)
        assert(len(curr_tgt) == curr_att.shape[0])
        input_tok = curr_inp + [args.separator] + curr_tgt
        input_ref = curr_ref
        input_att = ["1.000000" for i in range(len(curr_inp))] + ['0.000000'] + ["{:.6f}".format(a) for a in curr_att]
        assert(len(input_tok) == len(input_att))
        input_att.insert(0,"1.000000") #bos
        input_att.append("1.000000") #eos
        print(' '.join(input_tok) + "\t" + ' '.join(input_ref) + "\t" + ' '.join(input_att))

def nomatchfound(inp, ref):
    input_tok, _ = tokenizer.tokenize(inp)
    refer_tok, _ = tokenizer.tokenize(ref)
    atten_tok = ["1.000000" for i in range(len(input_tok))]
    assert(len(input_tok) == len(atten_tok))
    atten_tok.insert(0,"1.000000") #bos
    atten_tok.append("1.000000") #eos
    print(' '.join(input_tok) + "\t" + ' '.join(refer_tok) + "\t" + ' '.join(atten_tok))

def getmatch(match_score, match):
    score = float(match_score)
    pos = match.find("=")
    src,tgt = match[pos+1:].split('￭')
    return score, src, tgt

    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--model_dir', type=str, help='ONMT model dir', required=True)
    parser.add_argument('-b', '--bpe_model_path', type=str, help='BPE model path', required=True)
    parser.add_argument('-v', '--voc', type=str, help='Source/target vocabulary file', required=True)
    parser.add_argument('-t', '--temperature', type=float, default=1, help='Softmax temperature (def 1)')
    parser.add_argument('-B', '--batch_size', type=int, default=1, help='Batch size (def 1)')
    parser.add_argument('-n', '--max_n', type=int, default=0, help='Max number of similar examples per sentence (def 0)')
    parser.add_argument('-s', '--min_score', type=float, default=0.5, help='Min score to keep a similar example (def .50)')
    parser.add_argument('-l', '--layer', type=int, default=8, help='Encoder layer to use (def 8)')
    parser.add_argument('--inference', action='store_true', help='preparing input stream for inference')
    parser.add_argument('-sep', '--separator', type=str, default="｟fuzzymatch｠", help='Token used to separate input/target sentences')
    parser.add_argument('-log', default='info', help="Logging level [debug, info, warning, critical, error] (info)")
    args = parser.parse_args()
    create_logger('stderr',args.log)
    if args.inference:
        args.batch_size = 1
    
    tokenizer = pyonmttok.Tokenizer("aggressive", joiner_annotate=True, bpe_model_path=args.bpe_model_path) ### build tokenizer    
    model = opennmt.load_model(args.model_dir) ### build/restore model
    model.initialize({"source_vocabulary": args.voc, "target_vocabulary": args.voc})
    checkpoint = tf.train.Checkpoint(model=model)
    checkpoint.restore(tf.train.latest_checkpoint(args.model_dir))
    s = onmt_align(tokenizer, model, args.temperature) ### build similarity

    linp = []
    lref = []
    lsrc = []
    ltgt = []
    n_in = 0
    n_out1 = 0
    n_out2 = 0
    for line in sys.stdin:
        n_in += 1
        input_refer_matchs = line.rstrip("\n").split('\t')
        if len(input_refer_matchs) < 2:
            sys.stderr.write('error: input must conatin at least 2 fields (input and reference)\n')
            sys.exit()
        inp = input_refer_matchs.pop(0)
        ref = input_refer_matchs.pop(0)
        matchs = input_refer_matchs
        if len(matchs) < 2: ### no matchs found
            if args.inference:
                nomatchfound(inp, ref)
            continue
        if len(inp.split()) == 0 or len(ref.split()) == 0:
            if args.inference:
                nomatchfound(inp, ref)
            continue
        ok = False
        n = 0
        for i in range(0,len(matchs),2):
            score, src, tgt = getmatch(matchs[i],matchs[i+1])
            if score < args.min_score or n >= args.max_n:
                break
            if len(src.split()) == 0 or len(tgt.split()) == 0:
                continue
            linp.append(inp)
            lref.append(ref)
            lsrc.append(src)
            ltgt.append(tgt)
            n += 1
            n_out2 += 1
            ok = True
            if (len(lsrc) == args.batch_size):
                batch(linp, lref, lsrc, ltgt, s, args)
                linp = []
                lref = []
                lsrc = []
                ltgt = []
        if ok:
            n_out1 += 1
        else:
            if args.inference:
                nomatchfound(inp,ref)
            
    if len(lsrc):
        batch(linp, lref, lsrc, ltgt, s, args)
    sys.stderr.write('Done input {} sentences, {} considered, {} generated!\n'.format(n_in,n_out1,n_out2))

