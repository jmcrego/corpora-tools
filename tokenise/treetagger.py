#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#treetagger: https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/
#download in a single dir: tagger package, tagging scripts, install-tagger.sh and parameters files (as many as you want)
#run $> sh install-tagger.sh

#treetaggerwrapper: https://treetaggerwrapper.readthedocs.io/en/latest/
#$> pip3 install --user treetaggerwrapper

import sys
import treetaggerwrapper as ttpw

name = sys.argv.pop(0)
tagdir = ttpw.locate_treetagger()
lang = 'en'
sep = '￨'
usage = """usage: {} [-l LANG] [-sep STRING] < stdin > stdout
   -l     LANG : use: en, de, fr, es, ca (default {})
   -sep STRING : use STRING as separator (default {})
   -tagdir DIR : treetagger dir absolute path (default {})
   -h               : this message
Comments:
- A light tokenization is performed as first step (similar to (onmt) tokenize -m conservative
- Use python3
- Needs treetaggerwrapper
""".format(name,lang,sep,tagdir)

while len(sys.argv):
    tok = sys.argv.pop(0)
    if tok=="-l" and len(sys.argv):
        lang = sys.argv.pop(0)

    elif tok=="-sep" and len(sys.argv):
        sep = sys.argv.pop(0)

    elif tok=="-tagdir" and len(sys.argv):
        tagdir = sys.argv.pop(0)

    elif tok=="-h":
        sys.stderr.write("{}".format(usage))
        sys.exit()

    else:
        sys.stderr.write('error: unparsed {} option\n'.format(tok))
        sys.stderr.write("{}".format(usage))
        sys.exit()

if tagdir == "":
    sys.stderr.write('error: tree-tagger location was not found\n')
    sys.exit()

sys.stderr.write('lang=\'{}\' sep=\'{}\' tagdir=\'{}\'\n'.format(lang,sep,tagdir))
tagger = ttpw.TreeTagger(TAGLANG=lang, TAGDIR=tagdir)

for n,line in enumerate(sys.stdin):
    toks = tagger.tag_text(line.rstrip(),notagurl=True,notagemail=True,notagip=True,notagdns=True,nosgmlsplit=True)
    for t in range(len(toks)):
        tags = toks[t].split('\t')
        if len(tags) != 3:
            sys.stderr.write('warning: line={} tags={}\n'.format(n+1,' '.join(tags)))
        toks[t] = sep.join(tags)
    print(' '.join(toks))
