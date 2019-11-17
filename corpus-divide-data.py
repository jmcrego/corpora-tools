# -*- coding: utf-8 -*-

import random
import sys

def progress(n):
    if n%10000 == 0:
        if n%100000 == 0:
            sys.stderr.write("{}".format(n))
        else:
            sys.stderr.write(".")

def build_data_set(data,sname,indexs):
    for d in range(len(data)):
        with open(data[d]['name']+'.'+sname, "w") as f:
            for i in indexs:
                f.write(data[d]['lines'][i])    


#####################################################################
### MAIN ############################################################
#####################################################################

if __name__ == '__main__':

    name = sys.argv.pop(0)
    usage = '''usage: {} -files FILE -i FILE [-v]
   -files     FILE : files description 
   -i         FILE : data to split (default stdin)
   -pattern STRING : output pattern file
   -v              : verbose output

Ex: {} -files desc_files -i all_data.gdfa -pattern en2fr.gdfa
desc_files contains a sequence of files which joined form a file parallel to all_data.gdfa
Then, it splits data_all.gdfa into as many files as described in desc_files
with the names indicated in desc_files appending .pattern
'''.format(name,name)

    files = None
    fin = None
    pattern = None
    verbose = False
    while len(sys.argv):
        tok = sys.argv.pop(0)
        if tok=="-h":
            sys.stderr.write("{}".format(usage))
            sys.exit()
        elif tok=="-v":
            verbose = True
        elif tok=="-files" and len(sys.argv):
            files = sys.argv.pop(0)
        elif tok=="-i" and len(sys.argv):
            fin = sys.argv.pop(0)
        elif tok=="-pattern" and len(sys.argv):
            pattern = sys.argv.pop(0)
        else:
            sys.stderr.write('error: unparsed {} option\n'.format(tok))
            sys.stderr.write("{}".format(usage))
            sys.exit()

    if files is None:
        sys.stderr.write('error: missing -files option\n')
        sys.stderr.write("{}".format(usage))
        sys.exit()

    if pattern is None:
        sys.stderr.write('error: missing -pattern option\n')
        sys.stderr.write("{}".format(usage))
        sys.exit()

    total_len = 0
    file_names = [line.rstrip() for line in open(files, 'r')]
    file_lens = []
    for f in file_names:
        FILE = [line for line in open(f, 'r')]
        file_lens.append(len(FILE))
        total_len += file_lens[-1]
        sys.stderr.write('Read {} [{}] total={}\n'.format(f,file_lens[-1],total_len))
        
    Fin = [line for line in open(fin, 'r')]
    sys.stderr.write('Fin [{}]\n'.format(len(Fin)))

    if len(Fin) != total_len:
        sys.stderr.write('error: diff num of lines {} <> {}\n'.format(len(Fin),total_len))
        sys.exit()

    total_len = 0
    curr_nlines = 0
    curr_i = 0
    curr_fd = open(file_names[curr_i]+"."+pattern, 'w')
    for line in Fin:
        curr_fd.write(line)
        curr_nlines += 1
        if curr_nlines == file_lens[curr_i]:
            total_len += curr_nlines
            sys.stderr.write('Write {} [{}] total={}\n'.format(file_names[curr_i]+"."+pattern,curr_nlines,total_len))
            curr_fd.close()
            curr_nlines = 0
            curr_i += 1
            if curr_i == len(file_names):
                break
            curr_fd = open(file_names[curr_i]+"."+pattern, 'w')

    if len(Fin) != total_len:
        sys.stderr.write('error: diff num of lines {} <> {}\n'.format(len(Fin),total_len))
    sys.stderr.write('Done\n')
