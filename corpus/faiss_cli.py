# -*- coding: utf-8 -*-
import io
import sys
import gzip
import faiss
import logging
import numpy as np
from timeit import default_timer as timer

def create_logger(logfile, loglevel):
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        sys.stderr.write("Invalid log level={}\n".format(loglevel))
        sys.exit()
    if logfile is None or logfile == 'stderr':
        logging.basicConfig(format='[%(asctime)s.%(msecs)03d] %(levelname)s %(message)s', datefmt='%Y-%m-%d_%H:%M:%S', level=numeric_level)
        logging.info('Created Logger level={}'.format(loglevel))
    else:
        logging.basicConfig(filename=logfile, format='[%(asctime)s.%(msecs)03d] %(levelname)s %(message)s', datefmt='%Y-%m-%d_%H:%M:%S', level=numeric_level)
        logging.info('Created Logger level={} file={}'.format(loglevel, logfile))

class Infile:

    def __init__(self, file, d=0, norm=True,file_str=None):
        self.file = file
        self.vec = []
        self.txt = []
        self.d = d

        if file.endswith('.gz'): 
            f = gzip.open(file, 'rt')
        else:
            f = io.open(file, 'r', encoding='utf-8', newline='\n', errors='ignore')

        for l in f:
            l = l.rstrip().split(' ')
            if self.d > 0:
                if len(l) != self.d:
                    logging.error('found a vector with {} cells instead of {} in line {} of file {}'.format(len(l),self.d,len(self.vec)+1,self.file))
                    sys.exit()
            else:
                self.d = len(l)
            self.vec.append(l)

        logging.info('Read {} vectors ({} cells) from {}'.format(len(self.vec),self.d,self.file))
        self.vec = np.array(self.vec).astype('float32')

        if norm:
            faiss.normalize_L2(self.vec)
            logging.info('Vectors normalized')

        if file_str is None:
            return

        if file_str.endswith('.gz'): 
            f = gzip.open(file_str, 'rt')
        else:
            f = io.open(file_str, 'r', encoding='utf-8', newline='\n', errors='ignore')

        for l in f:
            self.txt.append(l.rstrip())
        logging.info('Read {} strings in {}'.format(len(self.txt),file_str))

        if len(self.txt) != len(self.vec):
            logging.error('diff num of entries {} <> {} in files {} and {}'.format(len(self.vec),len(self.txt),file, file_str))
            sys.exit()

    def __len__(self):
        return len(self.vec)

    def txts(self):
        return len(self.txt)>0


class IndexFaiss:

    def __init__(self, file, file_str=None):
        tstart = timer()
        self.file_db = file
        self.db = Infile(file, file_str=file_str)
        self.index = faiss.IndexFlatIP(self.db.d) #inner product (needs L2 normalization over db and query vectors)
        self.index.add(self.db.vec) #add all normalized vectors to the index
        tend = timer()
        sec_elapsed = (tend - tstart)
        vecs_per_sec = len(self.db.vec) / sec_elapsed
        logging.info('Read db with {} vectors in {} sec [{:.2f} vecs/sec]'.format(self.index.ntotal, sec_elapsed, vecs_per_sec))

    def Query(self,file,file_str,k,min_score,skip_same_id):
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
        logging.info('Read query + search with {} vectors in {} sec [{:.2f} vecs/sec]'.format(len(I), sec_elapsed, vecs_per_sec))

        results = [] * len(query)
        for i_query in range(len(I)): #for each sentence in query, retrieve the k-closest
            for j in range(len(I[i_query])):
                i_db = I[i_query,j]
                score = D[i_query,j]
                if score < min_score: ### skip
                    continue
                if skip_same_id and i_query == i_db: ### skip
                    continue
                results[i_query].append((score, i_db))

        return results


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

    fdb = []
    fquery = []
    fdb_str = []
    fquery_str = []
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
    -db         FILEs : file/s to index (comma-separated)
    -db_str     FILEs : file/s to index (comma-separated)
    -query      FILEs : file with queries (comma-separated)
    -query_str  FILEs : file with queries (comma-separated)
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
            fdb = sys.argv.pop(0).split(',')
        elif tok=="-db_str" and len(sys.argv):
            fdb_str = sys.argv.pop(0).split(',')
        elif tok=="-query" and len(sys.argv):
            fquery = sys.argv.pop(0).split(',')
        elif tok=="-query_str" and len(sys.argv):
            fquery_str = sys.argv.pop(0).split(',')
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

    if len(fdb) == 0:
        sys.stderr.write('error: missing -fdb option\n')
        sys.exit()

    if len(fquery) == 0:
        sys.stderr.write('error: missing -fquery option\n')
        sys.exit()

    if len(fdb_str) == 0:
        fdb_str = [None] * len(fdb)

    if len(fquery_str) == 0:
        fquery_str = [None] * len(fquery)

    if len(fdb_str) != len(fdb):
        sys.stderr.write('error: diff num of files between -fdb and -fdb_str\n')
        sys.exit()

    if len(fquery_str) != len(fquery):
        sys.stderr.write('error: diff num of files between -fquery and -fquery_str\n')
        sys.exit()


    indexdb = []
    for i_db in range(len(fdb)):
        indexdb.append(IndexFaiss(fdb[i_db],fdb_str[i_db]))

    for i_query in range(len(fquery)):
        if skip_same_id:
            k += 1
        for i_db in range(len(fdb)):
            indexdb[i_db].Query(fquery[i_query],fquery_str[i_query],k,min_score,skip_same_id)








