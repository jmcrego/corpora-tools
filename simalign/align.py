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

def get_tokenizer_model(model,device):
    model_class = BertModel
    tokenizer_class = BertTokenizer
    tokenizer = tokenizer_class.from_pretrained(model)
    emb_model = model_class.from_pretrained(model, output_hidden_states=True)
    emb_model.eval()
    emb_model.to(device)
    return tokenizer, emb_model
        
def matrix(lsim, ltgt, sim):
    #lsim = [tokenizer.decode([s]) for s in sim]
    #ltgt = [tokenizer.decode([t]) for t in tgt]
    maxl = max([len(x) for x in lsim+ltgt] + [4]) + 1
    for i in range(len(lsim)):
        lsim[i] += " "*(maxl - len(lsim[i]))
    for i in range(len(ltgt)):
        ltgt[i] += " "*(maxl - len(ltgt[i]))
    print(' '*maxl+''.join(ltgt))
    for i in range(sim.shape[0]):
        lsim_i = [lsim[i]]
        for j in range(sim.shape[1]):
            t = "{:.2f}".format(sim[i,j]) if sim[i,j] > 0.0 else ""
            lsim_i.append(t+ " "*(maxl - len(t)))
        print(''.join(lsim_i))


def reformat(ids,embed):
    '''
    discard tags (PAD, CLS, SEP)
    rejoin sub-tokens
    '''
    PAD = 0
    CLS = 101
    SEP = 102

    lids = [tokenizer.decode([s]) for s in ids]
    lstr = []
    lemb = []
    curr = 1
    while True:
        if ids[curr] == SEP or ids[curr] == PAD: ### end of sequence
            break
        last = curr + 1
        while ids[last] != SEP and ids[last] != PAD and lids[last].startswith("##"):
            last += 1
        lstr.append(''.join(lids[curr:last]).replace('##',''))
        lemb.append(np.average(embed[curr:last], axis=0))
        curr = last

    return lstr, np.asarray(lemb)

def process_batch(batch_src, batch_sim, batch_tgt, tokenizer, emb_model, args):
    inputs_sim = tokenizer(batch_sim, is_split_into_words=False, padding=True, truncation=True, return_tensors="pt")
    inputs_tgt = tokenizer(batch_tgt, is_split_into_words=False, padding=True, truncation=True, return_tensors="pt")
    hidden_sim = emb_model(**inputs_sim.to(device))["hidden_states"]
    hidden_tgt = emb_model(**inputs_tgt.to(device))["hidden_states"]
    if args.layer >= len(hidden_sim):
        raise ValueError("Specified to take embeddings from layer {}, but model has only {} layers.".format(args.layer,len(hidden_sim)))
    hidden_sim = hidden_sim[args.layer] # [bs, nsim, ed]
    hidden_tgt = hidden_tgt[args.layer] # [bs, ntgt, ed]
    for i in range(hidden_sim.shape[0]): ### for each sentence
        lsim, embed_sim = reformat(inputs_sim['input_ids'][i].detach().numpy(), hidden_sim[i])
        ltgt, embed_tgt = reformat(inputs_tgt['input_ids'][i].detach().numpy(), hidden_tgt[i])
        cosine = (cosine_similarity(embed_sim, embed_tgt) + 1.0 ) / 2.0 # [nsim, ntgt], ranges [0,+1] instead of [-1,+1]
        x = scipy.special.softmax(cosine/args.temperature, axis=1) ### softmax with temperature
        x = np.maximum(np.zeros_like(x), np.minimum(np.ones_like(x), args.slope*(x-args.min))) ### activation function
        matrix(lsim, ltgt, x)
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('fsrc', help='Input source file')
    parser.add_argument('fsim', help='Input similar file (with sentences similar to those in source file)')
    parser.add_argument('ftgt', help='Input target file (with translation of sentences in similar file)')
    parser.add_argument('-t', '--temperature', type=float, default=0.01, help='Softmax temperature (def 0.01)')
    parser.add_argument('-s', '--slope', type=float, default=1.0, help='Slope for activation function (def 1.0)')
    parser.add_argument('-m', '--min', type=float, default=0.1, help='Minimum for activation function (def 0.1)')
    parser.add_argument('-l', '--layer', type=int, default=8, help='Encoder layer to use (def 8)')
    parser.add_argument('-b', '--batch_size', type=int, default=1, help='Batch size (def 1)')
    parser.add_argument('-log', default='info', help="Logging level [debug, info, warning, critical, error] (info)")
    args = parser.parse_args()
    create_logger('stderr',args.log)

    device=torch.device('cpu')
    model = "bert-base-multilingual-cased"
    tokenizer, emb_model = get_tokenizer_model(model,device)

    with torch.no_grad():
        batch_src = []
        batch_sim = []
        batch_tgt = []
        with codecs.open(args.fsrc, 'r', 'utf-8') as fsrc, codecs.open(args.fsim, 'r', 'utf-8') as fsim, codecs.open(args.ftgt, 'r', 'utf-8') as ftgt:
            for lsrc, lsim, ltgt in zip(fsrc, fsim, ftgt):
                batch_src.append(lsrc.strip())
                batch_sim.append(lsim.strip())
                batch_tgt.append(ltgt.strip())
                if len(batch_src) == args.batch_size:
                    process_batch(batch_src, batch_sim, batch_tgt, tokenizer, emb_model, args)
                    batch_src = []
                    batch_sim = []
                    batch_tgt = []                    
            if len(batch_src):
                process_batch(batch_src, batch_sim, batch_tgt, tokenizer, emb_model, args)

