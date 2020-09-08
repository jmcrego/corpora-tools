# -*- coding: utf-8 -*-
import io
import sys
import gzip
import faiss
import logging
import numpy as np
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

    def __init__(self, file, d=0, norm=True):

        if file.find(','):
            self.file, self.file_str = file.split(',')
        else:
            self.file=file
            self.file_str = None

        self.vec = []    ### list with vectors found in file
        self.txt = []    ### list with strings found in file_str
        self.d = d       ### will contain length of vectors

        if self.file.endswith('.gz'): 
            f = gzip.open(self.file, 'rt')
        else:
            f = io.open(self.file, 'r', encoding='utf-8', newline='\n', errors='ignore')

        for l in f:
            l = l.rstrip().split(' ')
            if self.d > 0:
                if len(l) != self.d:
                    logging.error('found a vector with {} cells instead of {} in line {} of file {}'.format(len(l),self.d,len(self.vec)+1,self.file))
                    sys.exit()
            else:
                self.d = len(l)
            self.vec.append(l)

        self.vec = np.array(self.vec).astype('float32')

        logging.info('\tRead {} vectors ({} cells) from {}'.format(len(self.vec),self.d,self.file))

        if norm:
            faiss.normalize_L2(self.vec)
            logging.info('\tVectors normalized')

        if self.file_str is not None:

            if self.file_str.endswith('.gz'): 
                f = gzip.open(self.file_str, 'rt')
            else:
                f = io.open(self.file_str, 'r', encoding='utf-8', newline='\n', errors='ignore')

            for l in f:
                self.txt.append(l.rstrip())

            logging.info('\tRead strings from {}'.format(self.file_str))

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
        logging.info('Added DB with {} vectors ({} cells) in {} sec [{:.2f} vecs/sec]'.format(len(db.vec), db.d, sec_elapsed, vecs_per_sec))

    def Query(self,query,k,min_score,skip_same_id):
        results = [defaultdict(float)] * len(query) ### each query input string has associated a dictionary (string => score)
        for i_db in range(len(self.DB)):
            curr_db = self.DB[i_db]
            curr_index = self.INDEX[i_db]
            logging.info('Querying {} over {}'.format(query.file, curr_db.file))
            tstart = timer()
            D, I = curr_index.search(query.vec, k)
            assert len(D) == len(I)     #I[i,j] contains the index in db of the j-th closest sentence to the i-th sentence in query
            assert len(D) == len(query) #D[i,j] contains the corresponding score
            tend = timer()
            sec_elapsed = (tend - tstart)
            vecs_per_sec = len(I) / sec_elapsed
            logging.info('Found results in {} sec [{:.2f} vecs/sec]'.format(sec_elapsed, vecs_per_sec))

            for i_query in range(len(I)): #for each sentence in query, retrieve the k-closest
                for j in range(len(I[i_query])):
                    i_db = I[i_query,j]
                    score = D[i_query,j]
                    #print(score,i_db,curr_db.txt[i_db])
                    if score < min_score: ### skip
                        continue
                    if skip_same_id and i_query == i_db: ### skip
                        continue
                    txt = "{:.6f}：{}：{}：{}".format(score,j,i_db,curr_db.txt[i_db])
                    results[i_query][txt] = score

        for i_query in range(len(results)):
            res = results[i_query]
            out = []
            for txt, score in sorted(results[i_query].items(), key=lambda item: item[1], reverse=True):
                out.append('{}'.format(txt))
            print('\t'.join(out))


    def Query2(self,file,file_str,k,min_score,skip_same_id,skip_query,do_eval):
        tstart = timer()
        if file == self.file_db:
            query = self.db
        else:
            query = Infile(file, d=self.db.d, file_str=file_str)
        D, I = self.index.search(query.vec, k)
        assert len(D) == len(I)     #I[i,j] contains the index in db of the j-th closest sentence to the i-th sentence in query
        assert len(D) == len(query) #D[i,j] contains the corresponding score
        tend = timer()
        sec_elapsed = (tend - tstart)
        vecs_per_sec = len(I) / sec_elapsed
        logging.info('processed readquery+search with {} vectors in {} sec [{:.2f} vecs/sec]'.format(len(I), sec_elapsed, vecs_per_sec))
        
        if do_eval:
            n_ok = [0.0] * k

        for i_query in range(len(I)): #for each sentence in query
            ### to compute accuracy in case query is db
            if do_eval:
                for j in range(k):
                    if i_query in I[i_query,0:j+1] and D[i_query,0] >= min_score: #if the same index 'i' (current index) is found int the j-best retrieved sentences
                        n_ok[j] += 1.0
            ### output
            out = []
            if not skip_query:
                out.append(str(i_query+1))
                if query.txts():
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

        if do_eval:
            n_ok = ["{:.3f}".format(n/len(query)) for n in n_ok]
            logging.info('Done k-best Acc = [{}] over {} examples'.format(', '.join(n_ok),len(query)))
        else:
            logging.info('Done over {} examples'.format(len(query)))


if __name__ == '__main__':

    fDB = []
    fQUERY = []
    k = 1
    min_score = 0.5
    skip_same_id = False
    skip_query = False
    do_eval = False
    verbose = False
    log_file = None
    log_level = 'debug'
    name = sys.argv.pop(0)
    usage = '''usage: {} -db FILE -query FILE [-db_str FILE] [-query_str FILE] [-d INT] [-k INT] [-skip_same_id] [-skip_query] [-log_file FILE] [-log_level STRING]
    -db     FILE,FILE : db files with vectors/strings
    -query  FILE,FILE : query files with vectors/strings
    -k            INT : k-best to retrieve (default 1)
    -min_score  FLOAT : minimum distance to accept a match (default 0.5) 
    -skip_same_id     : do not consider matchs with db_id == query_id (k+1 matchs retrieved)
    -skip_query       : do not output query columns (query_index [query_str])
    -do_eval          : run evaluation (query_index == db_index)
    -log_file    FILE : verbose output (default False)
    -log_level STRING : verbose output (default False)
    -h                : this help
'''.format(name)


    while len(sys.argv):
        tok = sys.argv.pop(0)
        if tok=="-h":
            sys.stderr.write("{}".format(usage))
            sys.exit()
        elif tok=="-v":
            verbose = True
        elif tok=="-db" and len(sys.argv):
            fDB.append(sys.argv.pop(0))
        elif tok=="-query" and len(sys.argv):
            fQUERY.append(sys.argv.pop(0))
        elif tok=="-k" and len(sys.argv):
            k = int(sys.argv.pop(0))
        elif tok=="-min_score" and len(sys.argv):
            min_score = float(sys.argv.pop(0))
        elif tok=="-log_file" and len(sys.argv):
            log_file = sys.argv.pop(0)
        elif tok=="-log_level" and len(sys.argv):
            log_level = sys.argv.pop(0)
        elif tok=="-skip_same_id":
            skip_same_id = True
        elif tok=="-do_eval":
            do_eval = True
        elif tok=="-skip_query":
            skip_query = True
        else:
            sys.stderr.write('error: unparsed {} option\n'.format(tok))
            sys.stderr.write("{}".format(usage))
            sys.exit()

    create_logger(log_file,log_level)

    if len(fDB) == 0:
        logging.error('error: missing -fdb option')
        sys.exit()

    if len(fQUERY) == 0:
        logging.error('error: missing -fquery option')
        sys.exit()

    if skip_same_id:
        k += 1

    logging.info('READING DBs')
    indexfaiss = IndexFaiss()
    for i_db in range(len(fDB)):
        db = Infile(fDB[i_db], d=0, norm=True)
        indexfaiss.add_db(db)

    logging.info('PROCESSING Queries')
    for i_query in range(len(fQUERY)):
        query = Infile(fQUERY[i_query], d=0, norm=True)
        indexfaiss.Query(query,k,min_score,skip_same_id)









