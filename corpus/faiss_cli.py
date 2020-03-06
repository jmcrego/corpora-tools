# -*- coding: utf-8 -*-
import logging
import sys
import io
import gzip
import faiss
import torch
import copy
import numpy as np
from torch import nn
from torch.nn import functional as F
from faiss import normalize_L2

class Infile:

    def __init__(self, file, d, norm=True,file_str=None):
        self.file = file
        self.vec = []
        self.txt = []

        if file.endswith('.gz'): 
            f = gzip.open(file, 'rt')
        else:
            f = io.open(file, 'r', encoding='utf-8', newline='\n', errors='ignore')

        for l in f:
            l = l.rstrip().split(' ')
            if len(l) != d:
                logging.error('found {} floats instead of {}'.format(len(l),d))
                sys.exit()
            self.vec.append(l)

        sys.stderr.write('Read {} vectors in {}\n'.format(len(self.vec),file))
        self.vec = np.array(self.vec).astype('float32')

        if norm:
            faiss.normalize_L2(self.vec)
            sys.stderr.write('Vectors normalized\n')

        if file_str is None:
            return

        if file_str.endswith('.gz'): 
            f = gzip.open(file_str, 'rt')
        else:
            f = io.open(file_str, 'r', encoding='utf-8', newline='\n', errors='ignore')

        for l in f:
            self.txt.append(l.rstrip())
        sys.stderr.write('Read {} strings in {}\n'.format(len(self.txt),file_str))

        if len(self.txt) != len(self.vec):
            logging.error('diff num of entries {} <> {} in files {} and {}'.format(len(self.vec),len(self.txt),file, file_str))
            sys.exit()

    def __len__(self):
        return len(self.vec)

    def txts(self):
        return len(self.txt)>0


class IndexFaiss:

    def __init__(self, file, d, file_str=None):
        self.file_db = file
        self.db = Infile(file, d, norm=True, file_str=file_str)
        self.index = faiss.IndexFlatIP(d) #inner product (needs L2 normalization over db and query vectors)
        self.index.add(self.db.vec) # add all normalized vectors to the index
        logging.info("read {} vectors".format(self.index.ntotal))


    def Query(self,file,d,k,file_str,min_score,skip_same_id,skip_query):
        if file == self.file_db:
            query = copy.deepcopy(self.db)
        else:
            query = Infile(file, d, norm=True, file_str=file_str)
        D, I = self.index.search(query.vec, k)
        assert len(D) == len(I)
        assert len(D) == len(query)
        #I[i,j] contains the index in db of the j-th closest sentence to the i-th sentence in query
        #D[i,j] contains the corresponding score
        if file == self.file_db:
            n_ok = [0.0] * k

        for i_query in range(len(I)): #for each sentence in query
            ### to compute accuracy in case query is db
            if file == self.file_db:
                for j in range(k):
                    if i_query in I[i_query,0:j+1]: #if the same index 'i' (current index) is found int the j-best retrieved sentences
                        n_ok[j] += 1.0
            ### output
            out = []
            if not skip_query:
                out.append(str(i_query+1))
                if file_str is not None and query.txts():
                    out.append(query.txt[i_query])
            for j in range(len(I[i_query])):
                i_db = I[i_query,j]
                score = D[i_query,j]
                if score < min_score: ### skip
                    continue
                if skip_same_id and i_query == i_db: ### skip
                    continue
                out.append("{:.6f}：{}".format(score,i_db+1))
                if self.db.txts():
                    out.append(self.db.txt[i_db])
            print('\t'.join(out))

        if file == self.file_db:
            n_ok = ["{:.3f}".format(n/len(query)) for n in n_ok]
            sys.stderr.write('Done k-best Acc = [{}] over {} examples\n'.format(', '.join(n_ok),len(query)))
        else:
            sys.stderr.write('Done over {} examples\n'.format(len(query)))





'''
class Index:

    def __init__(self, file, d, file_str=None):
        self.db = Infile(file, d, norm=True, file_str=file_str)
        logging.info("read {} vectors".format(len(self.db)))


    def Query(self,file,d,k,file_str,verbose):
        #cos = nn.CosineSimilarity(dim=1, eps=1e-6)
        query = Infile(file, d, norm=True, file_str=file_str)
        db = torch.from_numpy(self.db.vec)
        D = []
        I = []
        for i in range(len(query)):
            q =  torch.from_numpy(query.vec[i]).unsqueeze(0)
            dist = F.cosine_similarity(db,q)
            dist_sorted, index_sorted = torch.sort(dist, descending=True)
            D.append(dist_sorted[:k].numpy())
            I.append(index_sorted[:k].numpy())
        results(np.array(D),np.array(I),k,self.db,query,verbose)
'''

if __name__ == '__main__':

    fdb = None
    fquery = None
    fdb_str = None
    fquery_str = None
    d = 512
    k = 1
    min_score = 0.1
    skip_same_id = False
    skip_query = False
    verbose = False
    name = sys.argv.pop(0)
    usage = '''usage: {} -db FILE -query FILE [-db_str FILE] [-query_str FILE] [-d INT] [-k INT] [-skip_same_id] [-skip_query] [-v]
    -db         FILE : file to index 
    -db_str     FILE : file to index 
    -query      FILE : file with queries
    -query_str  FILE : file with queries
    -d           INT : vector size (default 512)
    -k           INT : k-best to retrieve (default 1)
    -min_score FLOAT : minimum distance to accept a match (default 0.1) 
    -skip_same_id    : do not consider matchs with query_id == db_id (k+1 matchs retrieved)
    -skip_query      : do not output queries (initial columns)
    -v               : verbose output (default False)
    -h               : this help
'''.format(name)

    while len(sys.argv):
        tok = sys.argv.pop(0)
        if tok=="-h":
            sys.stderr.write("{}".format(usage))
            sys.exit()
        elif tok=="-v":
            verbose = True
        elif tok=="-db" and len(sys.argv):
            fdb = sys.argv.pop(0)
        elif tok=="-db_str" and len(sys.argv):
            fdb_str = sys.argv.pop(0)
        elif tok=="-query" and len(sys.argv):
            fquery = sys.argv.pop(0)
        elif tok=="-query_str" and len(sys.argv):
            fquery_str = sys.argv.pop(0)
        elif tok=="-k" and len(sys.argv):
            k = int(sys.argv.pop(0))
        elif tok=="-d" and len(sys.argv):
            d = int(sys.argv.pop(0))
        elif tok=="-min_score" and len(sys.argv):
            min_score = float(sys.argv.pop(0))
        elif tok=="-skip_same_id":
            skip_same_id = True
        elif tok=="-skip_query":
            skip_query = True
        else:
            sys.stderr.write('error: unparsed {} option\n'.format(tok))
            sys.stderr.write("{}".format(usage))
            sys.exit()


    if fdb is not None:
        indexdb = IndexFaiss(fdb,d,fdb_str)


    if fquery is not None:
        if skip_same_id:
            k += 1
        indexdb.Query(fquery,d,k,fquery_str,min_score,skip_same_id,skip_query)



