# -*- coding: utf-8 -*-
import MeCab
import sys
import numpy as np

def jitao_map(str):
    return str
    
token = False
parse = False
sep = '❘' #Casseau, U+2700 - U+27BF
oneline = False
usage = """usage: {} < file
   -tok     : do tokenization
   -pos     : do pos tagging
   -oneline : output a single line per sentence (default False)
   -sep CHR : use CHR as wrd/pos separator when -oneline (default '{}')
   -h               : this message
""".format(sys.argv.pop(0),sep)

while len(sys.argv):
    tok = sys.argv.pop(0)
    if tok=="-tok":
        token = True

    elif tok=="-pos":
        parse = True

    elif tok=="-oneline":
        oneline = True

    elif tok=="-oneline" and len(sys.argv):
        sep = sys.argv.pop(0)
        
    elif tok=="-h":
        sys.stderr.write("{}".format(usage))
        sys.exit()

    else:
        sys.stderr.write('error: unparsed {} option\n'.format(tok))
        sys.stderr.write("{}".format(usage))
        sys.exit()

if token:
    wakati = MeCab.Tagger("-Owakati")
if parse:
    chasen = MeCab.Tagger("-Ochasen")

nline = 0
if not oneline:
    sep = '\t'

for line in sys.stdin:
    nline += 1
    line = line.rstrip()
    if len(line)==0:
        sys.stderr.write('warning: line {} is empty\n'.format(nline))
        print()
        continue

    if token:
        res = wakati.parse(line).split()
        if oneline:
            print(' '.join(res))
        else:
            print('\n'.join(res) + "\n")

    if parse:
        snt = []
        res = chasen.parse(line)
        for idx,r in enumerate(res.split('\n')):
            tags = r.split('\t')
            if len(tags) >=4:
                snt.append(tags[0]+sep+tags[1]+sep+jitao_map(tags[3]))
        if oneline:
            print(' '.join(snt))
        else:
            print('\n'.join(snt) + "\n")

