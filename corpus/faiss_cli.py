# -*- coding: utf-8 -*-
import io
import sys
import gzip
import faiss
import logging
import numpy as np
import os
from collections import defaultdict
from timeit import default_timer as timer

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



class Infile:

    def __init__(self, file, d=0, norm=True, max_vec=1000000):
        logging.info('Reading {}'.format(file))

        self.file = file
        self.d = d     ### will contain length of vectors
        self.vec = []  ### list with all vectors found in file
        self.max_vec = max_vec

        if self.file.endswith('.gz'): 
            f = gzip.open(self.file, 'rt')
        else:
            f = io.open(self.file, 'r', encoding='utf-8', newline='\n', errors='ignore')

        for l in f:
            l = l.rstrip().split(' ')
            if self.d == 0:
                self.d = len(l)
            if len(l) != self.d:
                logging.error('found a vector with {} cells instead of {} in line {} of file {}'.format(len(l),self.d,len(self.vec)+1,self.file))
                sys.exit()
            self.vec.append(l)

        if self.max_vec == 0:
            self.vecs = [self.vec]
        else:
            self.vecs = [self.vec[i: i+self.max_vec] for i in range(0, len(self.vec), self.max_vec)]
        logging.info('\t\tRead {} vectors into {} chunks ({} cells)'.format(len(self.vec),len(self.vecs),self.d))

        for i in range(len(self.vecs)):
            self.vecs[i] = np.array(self.vecs[i]).astype('float32')
            logging.info('\t\tBuilt float32 array for chunk {} with {} vectors'.format(i,len(self.vecs[i])))
            if norm:
                faiss.normalize_L2(self.vecs[i])

#    def __len__(self):
#        return len(self.vec)

#    def nvectors():
#        return len(self.vec)



class IndexFaiss:

    def __init__(self, db):
        self.db = db #infile containing the db
        self.indexs = []
        for i in range(len(self.db.vecs)): #we use n different indexs (one for each db chunk)
            index = faiss.IndexFlatIP(self.db.d) #inner product (needs L2 normalization over db and query vectors)
            index.add(self.db.vecs[i]) #add all normalized vectors to the index
            self.indexs.append(index) 

    def Query(self,query,k_best):
        query_results = [] ### list of dicts (one dict for each line in this query file)
        for _ in range(len(query.vec)):
            query_results.append(defaultdict(float))

        for i_query in range(len(query.vecs)): #### chunk in query
            for i_db in range(len(self.indexs)): #### chunk in db

                curr_db_index = self.indexs[i_db]
                curr_query_vecs = query.vecs[i_query]
                tstart = timer()
                D, I = curr_db_index.search(curr_query_vecs, k_best+2) ### retrieve more than k in case the first are filtered out by max_score
                assert len(D) == len(I)               #I[i,j] contains the index in db of the j-th closest sentence to the i-th sentence in query
                assert len(D) == len(curr_query_vecs) #D[i,j] contains the corresponding score
                tend = timer()
                sec_elapsed = (tend - tstart)
                vecs_per_sec = len(I) / sec_elapsed
                logging.info('\t\tFound results for [i_query={},i_db={}] in {} sec [{:.2f} vecs/sec]'.format(i_query, i_db, sec_elapsed, vecs_per_sec))

                for n in range(len(I)): #for each sentence in this query chunk, retrieve the k-closest
                    n_query = n + (i_query * query.max_vec)
                    for j in range(len(I[n])): ### for each result of this sentence
                        n_db = I[n,j] + (i_db * self.db.max_vec)
                        score = D[n,j]
                        query_results[n_query][n_db] = score
                        #print('inserted n_query={} len={}'.format(n_query,len(query_results[n_query])))
                        if len(query_results[n_query]) >= k_best:
                            break

        return query_results



if __name__ == '__main__':

    fdb = None
    fqueries = []
    k = 1
    min_score = 0.0
    max_score = 9.9
    max_vec = 1000000
    verbose = False
    log_file = None
    log_level = 'debug'
    tag = None
    name = sys.argv.pop(0)
    usage = '''usage: {} -db FILE [-query FILE]+ -tag STRING [-k INT] [-min_score FLOAT] [-max_score FLOAT] [-log_file FILE] [-log_level STRING]
    -db          FILE : db file with vectors
    -query       FILE : query file/s with vectors
    -tag       STRING : use [query].[tag] to output matches (default stdout)

    -k            INT : k-best to retrieve (default 1)
    -min_score  FLOAT : minimum distance to accept a match (default 0.0) 
    -max_score  FLOAT : maximum distance to accept a match (default 9.9) 
    -max_vec     INT : maximum vector length (default 1000000)

    -log_file    FILE : verbose output (default False)
    -log_level STRING : verbose output (default False)
    -h                : this help

Use -max_score 0.9999 to prevent perfect matches (perfect scores may exceed 1.0)

Output lines are parallel to query files and contain the corresponding k most similar db sentences:
score_1 \\t line_1 \\t score_2 \\t line_2 \\t ... \\t score_k \\t line_k

score is the similarity value (FLOAT)
line is [i_db,]n_db
- i_db indicates the i-th db file
- n_db indicates the n-th line in the i-th db file

All indexs start by 0
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
        elif tok=="-query" and len(sys.argv):
            fqueries.append(sys.argv.pop(0))
        elif tok=="-k" and len(sys.argv):
            k = int(sys.argv.pop(0))
        elif tok=="-max_vec" and len(sys.argv):
            max_vec = int(sys.argv.pop(0))
        elif tok=="-min_score" and len(sys.argv):
            min_score = float(sys.argv.pop(0))
        elif tok=="-max_score" and len(sys.argv):
            max_score = float(sys.argv.pop(0))
        elif tok=="-log_file" and len(sys.argv):
            log_file = sys.argv.pop(0)
        elif tok=="-log_level" and len(sys.argv):
            log_level = sys.argv.pop(0)
        elif tok=="-tag" and len(sys.argv):
            tag = sys.argv.pop(0)
        else:
            sys.stderr.write('error: unparsed {} option\n'.format(tok))
            sys.stderr.write("{}".format(usage))
            sys.exit()

    create_logger(log_file,log_level)

    if fdb is None:
        logging.error('error: missing -db option')
        sys.exit()

    if len(fqueries) == 0:
        logging.error('error: missing -query option')
        sys.exit()

    if tag is None:
        logging.error('error: missing -tag option')
        sys.exit()

    logging.info('*** Read DB ***')
    indexfaiss = IndexFaiss(Infile(fdb, d=0, norm=True, max_vec=max_vec))

    logging.info('*** Read Queries ***')
    for fquery in fqueries:
        query = Infile(fquery, d=0, norm=True, max_vec=max_vec)
        results = indexfaiss.Query(query,k)
        with open(fquery+'.'+tag, "w") as fout:
            for result in results: ### one line per query line
                res = []
                for n_query, score in sorted(result.items(), key=lambda item: item[1], reverse=True):
                    if score < min_score:
                        break
                    if score > max_score:
                        continue
                    res.append("{:.6f}\t{}".format(score,n_query))
                    if len(res) >= k:
                        break
                fout.write('\t'.join(res) + '\n')
        logging.info('Dumped {}-bests in {}'.format(k,fquery+'.'+tag))
 







