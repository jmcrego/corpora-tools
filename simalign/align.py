#coding=utf-8

#pip install torch
#pip install simalign

import os
import sys
import scipy
import torch
import codecs
import logging
import argparse
import numpy as np
import edit_distance
from copy import deepcopy
from sklearn.metrics.pairwise import cosine_similarity
from transformers import BertModel, BertTokenizer, XLMModel, XLMTokenizer, RobertaModel, RobertaTokenizer, XLMRobertaModel, XLMRobertaTokenizer

def create_logger(logfile, loglevel):
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        logging.error("Invalid log level={}".format(loglevel))
        sys.exit()
    if logfile is None or logfile == "stderr":
        logging.basicConfig(format="[%(asctime)s.%(msecs)03d] %(levelname)s %(message)s", datefmt="%Y-%m-%d_%H:%M:%S", level=numeric_level,)
    else:
        logging.basicConfig(filename=logfile, format="[%(asctime)s.%(msecs)03d] %(levelname)s %(message)s", datefmt="%Y-%m-%d_%H:%M:%S", level=numeric_level,)

def unrelated(l1, l2):
    if (len(l1) == 1 and len(l1[0]) == 0) or (len(l2) == 1 and len(l2[0]) == 0):
        return [0] * len(l2)
    sm = edit_distance.SequenceMatcher(a=[s.casefold() for s in l1], b=[s.casefold() for s in l2], action_function=edit_distance.highest_match_action)
    ### initially all non-related
    L2 = [0] * len(l2)
    for (code, b1, e1, b2, e2) in sm.get_opcodes():
        if code == 'equal': ### keep words
            L2[b2] = 1
    return L2

def get_tokenizer_model(model,device):
    model_class = BertModel
    tokenizer_class = BertTokenizer
    tokenizer = tokenizer_class.from_pretrained(model)
    emb_model = model_class.from_pretrained(model, output_hidden_states=True)
    emb_model.eval()
    emb_model.to(device)
    return tokenizer, emb_model
        
def matrix(usim, lsim, ltgt, x, y):
    lsim = deepcopy(lsim) #lsim : [nsim]
    ltgt = deepcopy(ltgt) #ltgt : [ntgt]
    size_score = 4 #size of each score {:.2f}
    size_cell = max([len(x) for x in lsim+ltgt] + [size_score]) + 1
    for s in range(len(lsim)):
        lsim[s] += " "*(size_cell - len(lsim[s]))
    for t in range(len(ltgt)):
        ltgt[t] += " "*(size_cell - len(ltgt[t]))
    lusim = []
    for s in range(len(usim)):
        lusim.append(str(usim[s]) + " "*(size_cell - 1))

    logging.debug(' '*size_cell+''.join(lusim))
    logging.debug(' '*size_cell+''.join(lsim)+'ATTENTION')
    for t in range(x.shape[0]):
        ltgt_t = []
        for s in range(x.shape[1]):
            ltgt_t.append("{:.2f}".format(x[t,s]) + " "*(size_cell - size_score))
        logging.debug(ltgt[t] + ''.join(ltgt_t) + "{:.7f}".format(y[t]))


def join_avg_subtokens(ids,embed):
    lids = [tokenizer.decode([s]) for s in ids]
    lstr = []
    lemb = []
    curr = 0
    while True:
        if curr == ids.shape[0]: ### end of sequence
            break
        last = curr + 1
        while last < ids.shape[0] and lids[last].startswith("##"):
            last += 1
        ###
        ### join tokens from curr to last-1
        ###
        lstr.append(''.join(lids[curr:last]).replace('##',''))
        if embed is not None:
            lemb.append(np.average(embed[curr:last], axis=0))
        curr = last
    return lstr, np.asarray(lemb)

def process_triplet(src, sim, tgt, tokenizer, emb_model, args):
    ### (sub-0tokenize src/sim/tgt sentences
    src_stok = tokenizer(src, is_split_into_words=True, padding=False, truncation=False, return_tensors="pt", add_special_tokens=False, verbose=False)
    sim_stok = tokenizer(sim, is_split_into_words=True, padding=False, truncation=False, return_tensors="pt", add_special_tokens=False, verbose=False)
    tgt_stok = tokenizer(tgt, is_split_into_words=True, padding=False, truncation=False, return_tensors="pt", add_special_tokens=False, verbose=False)

    ### get idx's of src/sim/tgt
    src_stok_ids = np.asarray(src_stok['input_ids'][0]) #[nsrc]
    sim_stok_ids = np.asarray(sim_stok['input_ids'][0]) #[nsim]
    tgt_stok_ids = np.asarray(tgt_stok['input_ids'][0]) #[ntgt]

    ### apply the model on tokenized sim/tgt sentences
    sim_stok_hidden = emb_model(**sim_stok.to(device))["hidden_states"]
    tgt_stok_hidden = emb_model(**tgt_stok.to(device))["hidden_states"]

    ### get the hidden layer of sim/tgt
    if args.layer >= len(sim_stok_hidden):
        raise ValueError("Specified to take embeddings from layer {}, but model has only {} layers.".format(args.layer,len(sim_stok_hidden)))
    sim_stok_hidden = np.asarray(sim_stok_hidden[args.layer].squeeze()) # [nsim, ed]
    tgt_stok_hidden = np.asarray(tgt_stok_hidden[args.layer].squeeze()) # [ntgt, ed]

    ### rejoin subtokenized words and average their embeddings
    src_tok, _              = join_avg_subtokens(src_stok_ids, None)            # [nsrc] 
    sim_tok, sim_tok_hidden = join_avg_subtokens(sim_stok_ids, sim_stok_hidden) # [nsim] [nsim, ed]
    tgt_tok, tgt_tok_hidden = join_avg_subtokens(tgt_stok_ids, tgt_stok_hidden) # [ntgt] [ntgt, ed]

    logging.debug('SRC: '+' '.join(src_tok))
    logging.debug('TGT: '+' '.join(tgt_tok))

    if len(tgt_tok) == 0:
        print(' '.join(src_tok))

    ### find unrelated words between sim/src sentences
    sim_tok_unrelated = unrelated(src_tok,sim_tok) #[ntgt]
    logging.debug('SIM: '+' '.join([str(sim_tok_unrelated[i])+":"+sim_tok[i] for i in range(len(sim_tok))]) )
    
    x = cosine_similarity(tgt_tok_hidden, sim_tok_hidden) # [ntgt, nsim]
    x = (x + 1.0) / 2.0 #ranges [0,+1] instead of [-1,+1]
    x = scipy.special.softmax(x/args.temperature, axis=1) # [ntgt, nsim] softmax with temperature
    x = np.maximum(np.zeros_like(x), np.minimum(np.ones_like(x), args.slope*(x-args.min))) ### [ntgt, nsim] activation function
    w = np.expand_dims(np.asarray(sim_tok_unrelated), axis=1) #[nsim,1]
    y = np.matmul(x, w).squeeze() #[ntgt, nsim] x [nsim, 1] = [ntgt]
    if args.log == 'debug':
        matrix(sim_tok_unrelated, sim_tok, tgt_tok, x, y)
    logging.debug('ATT: '+' '.join(["{}:{:.2f}".format(tgt_tok[i],y[i]) for i in range(len(tgt_tok))]))
    print(' '.join(src_tok) + "\t" + ' '.join(tgt_tok) + "\t" + ' '.join(["{:.6f}".format(y[i]) for i in range(y.shape[0])]))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('fsrc', help='SOURCE file (one sentence per line)')
    parser.add_argument('fsim', help='SIMILAR file (with sentences similar to those in source file)')
    parser.add_argument('ftgt', help='TARGET file (with translation of sentences in similar file)')
    parser.add_argument('-t', '--temperature', type=float, default=0.01, help='Softmax temperature (def 0.01)')
    parser.add_argument('-s', '--slope', type=float, default=1.0, help='Slope for activation function (def 1.0)')
    parser.add_argument('-m', '--min', type=float, default=0.0, help='Minimum for activation function (def 0.0)')
    parser.add_argument('-l', '--layer', type=int, default=8, help='Encoder layer to use (def 8)')
    parser.add_argument('-log', default='info', help="Logging level [debug, info, warning, critical, error] (info)")
    args = parser.parse_args()
    create_logger('stderr',args.log)

    device=torch.device('cpu')
    model = "bert-base-multilingual-cased"
    tokenizer, emb_model = get_tokenizer_model(model,device)

    with torch.no_grad():
        with codecs.open(args.fsrc, 'r', 'utf-8') as fsrc, codecs.open(args.fsim, 'r', 'utf-8') as fsim, codecs.open(args.ftgt, 'r', 'utf-8') as ftgt:
            for src, sim, tgt in zip(fsrc, fsim, ftgt):
                process_triplet(src, sim, tgt, tokenizer, emb_model, args)







