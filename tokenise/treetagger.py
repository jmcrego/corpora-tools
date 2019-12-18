#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#treetagger: https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/
#download in a single dir: tagger package, tagging scripts, install-tagger.sh and parameters files (as many as you want)
#run $> sh install-tagger.sh

#treetaggerwrapper: https://treetaggerwrapper.readthedocs.io/en/latest/
#$> pip3 install --user treetaggerwrapper

import sys
import treetaggerwrapper as ttpw

usage = """usage: {} [-l LANG] [-sep STRING] < stdin > stdout
   -l     LANG : use: en, de, fr, es, ca (default en)
   -sep STRING : use STRING as separator (default ￨)
   -tagdir DIR : treetagger dir absolute path (default /home/crego/progs/tree-tagger)
   -h               : this message
Comments:
- A light tokenization is performed as first step (similar to (onmt) tokenize -m conservative
- Use python3
- Needs treetaggerwrapper
""".format(sys.argv.pop(0))

lang = 'en'
sep = '￨'
tagdir = None
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

sys.stderr.write('lang={} sep={} tagdir={}\n'.format(lang,sep,tagdir))
if tagdir is None:
    tagger = ttpw.TreeTagger(TAGLANG=lang) ### TAGDIR is not needed if accessible
else:
    tagger = ttpw.TreeTagger(TAGLANG=lang, TAGDIR=tagdir)

for n,line in enumerate(sys.stdin):
    line = line.rstrip()
    #toks = ttpw.make_tags(tagger.tag_text(line))
    toks = tagger.tag_text(line,notagurl=True,notagemail=True,notagip=True,notagdns=True,nosgmlsplit=True)
    for t in range(len(toks)):
        tags = toks[t].split('\t')
        if len(tags) != 3:
            sys.stderr.write('warning: line={} tags={}\n'.format(n+1,' '.join(tags)))
        toks[t] = sep.join(tags)
    print(' '.join(toks))
    #if (len(line.split(' ')) != len(toks)): sys.stderr.write('warning: diff num of tokens in line={}\n{}\n{}\n'.format(n+1,line,' '.join(toks)))
