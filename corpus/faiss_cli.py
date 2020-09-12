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

        self.file = file
        self.d = d     ### will contain length of vectors
        vec = []      ### list with vectors found in file

        if self.file.endswith('.gz'): 
            f = gzip.open(self.file, 'rt')
        else:
            f = io.open(self.file, 'r', encoding='utf-8', newline='\n', errors='ignore')

        for l in f:
            l = l.rstrip().split(' ')
            if self.d == 0:
                self.d = len(l)
            if len(l) != self.d:
                logging.error('found a vector with {} cells instead of {} in line {} of file {}'.format(len(l),self.d,len(vec)+1,self.file))
                sys.exit()
            vec.append(l)

        self.vecs = [vec[i: i+max_vec] for i in range(0, len(vec), max_vec)]

        logging.info('\t\tRead {} vectors ({} cells) into {} chunks from {}'.format(len(vec),self.d,len(self.vecs),self.file))

        sys.exit()

        vec = np.array(vec).astype('float32')
        logging.info('\t\tCreated float32 array')

        if norm:
            faiss.normalize_L2(self.vec)
            logging.info('\t\tVectors normalized')

        if self.file_str is not None:

            if self.file_str.endswith('.gz'): 
                f = gzip.open(self.file_str, 'rt')
            else:
                f = io.open(self.file_str, 'r', encoding='utf-8', newline='\n', errors='ignore')

            for l in f:
                self.txt.append(l.rstrip())

            logging.info('\t\tRead strings from {}'.format(self.file_str))

            if len(self.txt) != len(self.vec):
                logging.error('diff num of entries {} <> {} in files {} and {}'.format(len(self.vec),len(self.txt), self.file, self.file_str))
                sys.exit()

    def __len__(self):
        return len(self.vec)

    def nvectors():
        return len(self.vec)

    def ncells():
        return len(self.d)

    def txts(self):
        return len(self.txt)>0



class IndexFaiss:

    def __init__(self):
        self.DB = []
        self.INDEX = []

    def add_db(self, db):
        #file is the name of the file
        #db is the Infile containing the file
        tstart = timer()
        index = faiss.IndexFlatIP(db.d) #inner product (needs L2 normalization over db and query vectors)
        index.add(db.vec)               #add all normalized vectors to the index
        tend = timer()
        sec_elapsed = tend - tstart
        vecs_per_sec = len(db.vec) / sec_elapsed
        self.DB.append(db)
        self.INDEX.append(index) 
        logging.info('Indexed DB with {} vectors ({} cells) in {} sec [{:.2f} vecs/sec]'.format(len(db.vec), db.d, sec_elapsed, vecs_per_sec))

    def Query(self,i_query,query,k,min_score,max_score,fin,tag):
        results = []
        resultsUniq = []
        for _ in range(len(query)):
            d = defaultdict(float)
            results.append(d)
            duniq = set()
            resultsUniq.append(duniq) #for a fast access to strings presents in resultsUniq[i]

        for i_db in range(len(self.DB)):
            curr_db = self.DB[i_db]
            curr_index = self.INDEX[i_db]
            logging.info('\t\tQuery={} over db={}'.format(query.file, curr_db.file))
            tstart = timer()
            D, I = curr_index.search(query.vec, k+5) ### retrieve more tha k in case the first are filtered out by (min_score, max_score)
            assert len(D) == len(I)     #I[i,j] contains the index in db of the j-th closest sentence to the i-th sentence in query
            assert len(D) == len(query) #D[i,j] contains the corresponding score
            tend = timer()
            sec_elapsed = (tend - tstart)
            vecs_per_sec = len(I) / sec_elapsed
            logging.info('Found results in {} sec [{:.2f} vecs/sec]'.format(sec_elapsed, vecs_per_sec))
            for n_query in range(len(I)): #for each sentence in query, retrieve the k-closest
                for j in range(len(I[n_query])):
                    n_db = I[n_query,j]
                    score = D[n_query,j]
                    if score < min_score or score > max_score: ### skip
                        continue
                    if curr_db.txts():
                        key = "{:.6f}：({},{})：({},{})：{}".format(score,i_query,n_query,i_db,n_db,curr_db.txt[n_db])
                        txt = curr_db.txt[n_db]
                        if txt in resultsUniq[n_query]:
                            continue
                        resultsUniq[n_query].add(txt)
                    else:
                        key = "{:.6f}：({},{})：({},{})".format(score,i_query,n_query,i_db,n_db)
                    results[n_query][key] = score
                    #print("{} {}".format(n_query,key))
                    if len(results[n_query]) >= k:
                        break

        if tag is not None:
            logging.info('Building results in {}'.format(fin+'.'+tag))
            F = open(fin+'.'+tag,"w") 

        for n_query in range(len(results)):
            result = results[n_query] ### defaultdict
            out = []
            for key, _ in sorted(result.items(), key=lambda item: item[1], reverse=True):
                out.append(key)
                if len(out) >= k:
                    break
            if tag is not None:
                F.write('\t'.join(out) + '\n')
            else:
                print('\t'.join(out))

        if tag is not None:
            F.close()



if __name__ == '__main__':

    fDB = None
    fQUERY = []
    k = 1
    min_score = 0.0
    max_score = 1.0
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
    -max_score  FLOAT : maximum distance to accept a match (default 1.0) 
    -max_vec     INT : maximum vector length (default 1000000)

    -log_file    FILE : verbose output (default False)
    -log_level STRING : verbose output (default False)
    -h                : this help

Use -max_score 0.9999 to prevent perfect matches

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
            fDB = sys.argv.pop(0)
        elif tok=="-query" and len(sys.argv):
            fQUERY.append(sys.argv.pop(0))
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

    if fDB is None:
        logging.error('error: missing -fdb option')
        sys.exit()

    if len(fQUERY) == 0:
        logging.error('error: missing -fquery option')
        sys.exit()

    if tag is None:
        logging.error('error: missing -tag option')
        sys.exit()

    logging.info('READING DB')
    indexfaiss = IndexFaiss()
    db = Infile(fDB, d=0, norm=True, max_vec=max_vec)
    indexfaiss.add_db(db)

    logging.info('PROCESSING Queries')
    for i_query in range(len(fQUERY)):
        query = Infile(fQUERY[i_query], d=0, norm=True)
        indexfaiss.Query(i_query,query,k,min_score,max_score,fQUERY[i_query],tag)









