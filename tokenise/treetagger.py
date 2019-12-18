#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#read documentation of treetaggerwrapper: https://treetaggerwrapper.readthedocs.io/en/latest/
import sys
import treetaggerwrapper as ttpw

usage = """usage: {} [-l LANG] [-sep STRING] < stdin > stdout
   -l     LANG : use: en, de, fr, es, ca (default en)
   -sep STRING : use STRING as separator (default ￨)
   -dir    DIR : treetagger dir (default ~/progs/tree-tagger)
   -h               : this message
""".format(sys.argv.pop(0))

lang = 'en'
sep = '￨'
tdir =  '~/progs/tree-tagger'
while len(sys.argv):
    tok = sys.argv.pop(0)
    if tok=="-l" and len(sys.argv):
        lang = sys.argv.pop(0)

    elif tok=="-sep" and len(sys.argv):
        sep = sys.argv.pop(0)

    elif tok=="-dir" and len(sys.argv):
        tdir = sys.argv.pop(0)

    elif tok=="-h":
        sys.stderr.write("{}".format(usage))
        sys.exit()

    else:
        sys.stderr.write('error: unparsed {} option\n'.format(tok))
        sys.stderr.write("{}".format(usage))
        sys.exit()

#tagger = ttpw.TreeTagger(TAGLANG=lang) ### TAGDIR is not needed if accessed otherwise
tagger = ttpw.TreeTagger(TAGLANG=lang, TAGDIR=tdir)

for n,line in enumerate(sys.stdin):
    line = line.rstrip()
    #toks = ttpw.make_tags(tagger.tag_text(line))
    toks = tagger.tag_text(line,notagurl=True,notagemail=True,notagip=True,notagdns=True,nosgmlsplit=True)
    for t in range(len(toks)):
        toks[t] = sep.join(toks[t].split('\t'))
    print(' '.join(toks))
    #if (len(line.split(' ')) != len(toks)): sys.stderr.write('warning: diff num of tokens in line={}\n{}\n{}\n'.format(n+1,line,' '.join(toks)))
