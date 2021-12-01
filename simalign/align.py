#coding=utf-8

#pip install torch
#pip install simalign

import os
import sys
#import scipy
import torch
import codecs
import argparse
#import numpy as np
#import edit_distance
#from copy import deepcopy
from simalign import SentenceAligner
#from sklearn.metrics.pairwise import cosine_similarity
from transformers import BertModel, BertTokenizer, XLMModel, XLMTokenizer, RobertaModel, RobertaTokenizer, XLMRobertaModel, XLMRobertaTokenizer

def get_tokenizer_model(model,device):
    model_class = BertModel
    tokenizer_class = BertTokenizer
    tokenizer = tokenizer_class.from_pretrained(model)
    emb_model = model_class.from_pretrained(model, output_hidden_states=True)
    emb_model.eval()
    emb_model.to(device)
    return tokenizer, emb_model

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('fsrc', help='SOURCE file (one sentence per line)')
    parser.add_argument('ftgt', help='TARGET file (with translations)')
    parser.add_argument('-mod', default='m', help="Alignment model to use: 'm':mwmf, 'a':inter, 'i':itermax, 'f':fwd, 'r':rev (default m)")
    args = parser.parse_args()

#    device=torch.device('cpu')
#    model = "bert-base-multilingual-cased"
#    tokenizer, emb_model = get_tokenizer_model(model,device)
    myaligner = SentenceAligner(model="bert", token_type="bpe", matching_methods=args.mod) 

    with torch.no_grad():
        with codecs.open(args.fsrc, 'r', 'utf-8') as fsrc, codecs.open(args.ftgt, 'r', 'utf-8') as ftgt:
            for src, tgt in zip(fsrc, ftgt):
                alignments = myaligner.get_word_aligns(src, tgt)
                for name in alignments:
                    print(' '.join(["{}-{}".format(a[0],a[1]) for a in alignments[name]]))





