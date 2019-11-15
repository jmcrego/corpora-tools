# -*- coding: utf-8 -*-

import sys
#from random import shuffle
import random
import pyonmttok

def progress(n_line):
    if n_line%10000 == 0:
        if n_line%100000 == 0:
            sys.stderr.write("{}".format(n_line))
        else:
            sys.stderr.write(".")

#####################################################################
### MAIN ############################################################
#####################################################################

if __name__ == '__main__':

    Min = 1
    Max = 99
    Maxw = 99
    Fert = 6.0
    Uniq = False
    Equals = False
    tok_mode = None
    seed = None
    fs = None
    ft = None
    dout = None
    tag = 'clean_min{}_max{}_maxw{}_fert{}_uniq{}_equals{}_tok{}_seed{}'.format(Min,Max,Maxw,Fert,Uniq,Equals,tok_mode,seed)
    verbose = False
    name = sys.argv.pop(0)
    usage = '''usage: {} -src FILE -tgt FILE [-out STRING] [-tag STRING] [-min INT] [-max INT] [-maxw INT] [-fert FLOAT] [-uniq] [-equals] [-seed INT]
   -src   FILE : input source file
   -tgt   FILE : input target file
   -tag STRING : output files are built adding this prefix to the original file names (default {})
   -out STRING : place filtered files in this directory (default {}:same as original files)

   -tok   MODE : use pyonmttok tokenizer aggressive|conservative|space before filtering (default {})
   -min    INT : discard if src/tgt contains less than [min] words (default {})*
   -max    INT : discard if src/tgt contains more than [max] words (default {})*
   -maxw   INT : discard if src/tgt contains a token with more than [maxw] characters (default {})*
   -fert FLOAT : discard if src/tgt is [fert] times bigger than tgt/src (default {})*
   -uniq       : discard repeated sentence pairs (default {})
   -equals     : discard if src equals to tgt (default {})

   -seed   INT : seed for random shuffle (default {}). Do not set to avoid shuffling
   -v          : verbose output (default False)
   -h          : this help

* set to 0 for no filtering
The script needs pyonmttok installed (pip install pyonmttok)
Output files are tokenised following opennmt tokenizer 'space' mode
'''.format(name,tag,dout,tok_mode,Min,Max,Maxw,Fert,Uniq,Equals,seed)
    tag = None

    while len(sys.argv):
        tok = sys.argv.pop(0)
        if tok=="-h":
            sys.stderr.write("{}".format(usage))
            sys.exit()
        elif tok=="-v":
            verbose = True
        elif tok=="-src" and len(sys.argv):
            fs = sys.argv.pop(0)
        elif tok=="-tgt" and len(sys.argv):
            ft = sys.argv.pop(0)
        elif tok=="-tag" and len(sys.argv):
            tag = sys.argv.pop(0)
        elif tok=="-out" and len(sys.argv):
            dout = sys.argv.pop(0)
        elif tok=="-min" and len(sys.argv):
            Min = int(sys.argv.pop(0))
        elif tok=="-max" and len(sys.argv):
            Max = int(sys.argv.pop(0))
        elif tok=="-maxw" and len(sys.argv):
            Maxw = int(sys.argv.pop(0))
        elif tok=="-fert" and len(sys.argv):
            Fert = float(sys.argv.pop(0))
        elif tok=="-tok" and len(sys.argv):
            tok_mode = sys.argv.pop(0)
        elif tok=="-uniq":
            Uniq = True
        elif tok=="-equals":
            Equals = True
        elif tok=="-seed" and len(sys.argv):
            seed = int(sys.argv.pop(0))
        else:
            sys.stderr.write('error: unparsed {} option\n'.format(tok))
            sys.stderr.write("{}".format(usage))
            sys.exit()

    if fs is None:
        sys.stderr.write('error: missing -s option\n')
        sys.stderr.write("{}".format(usage))
        sys.exit()

    if ft is None:
        sys.stderr.write('error: missing -t option\n')
        sys.stderr.write("{}".format(usage))
        sys.exit()

    if tag is None:
        tag = 'clean_min{}_max{}_maxw{}_fert{}_uniq{}_equals{}_tok{}_seed{}'.format(Min,Max,Maxw,Fert,Uniq,Equals,tok_mode,seed)

    tokenizer_space = pyonmttok.Tokenizer('space', joiner_annotate=False)
    if tok_mode is not None:
        tokenizer = pyonmttok.Tokenizer(tok_mode, joiner_annotate=False)

    f = open(fs,'r')
    src = [x.decode("utf-8-sig").encode("utf-8").rstrip() for x in f] ### decode and encode are to get rid of BOM
    f.close()
    sys.stderr.write('Read {}\n'.format(fs))

    f = open(ft,'r')
    tgt = [x.decode("utf-8-sig").encode("utf-8").rstrip() for x in f] ### decode and encode are to get rid of BOM
    f.close()
    sys.stderr.write('Read {}\n'.format(ft))

    if len(src) != len(tgt):
        sys.stderr.write('error: diff num of sentences in source/target files!\n')
        sys.exit()

    FS = fs.split('/')
    FS[-1] = tag + '.' + FS[-1]    
    if dout is not None:
        fs = open(dout+'/'+FS[-1],'w')
    else:
        fs = open('/'.join(FS),'w')

    FT = ft.split('/')
    FT[-1] = tag + '.' + FT[-1]
    if dout is not None:
        ft = open(dout+'/'+FT[-1],'w')
    else:
        ft = open('/'.join(FT),'w')

    output = set()
    nEquals = 0
    nMin = 0
    nMax = 0
    nMaxw = 0
    nFert = 0
    nUniq = 0
    n_output = 0
    indexs = [i for i in range(len(src))]
    if seed is not None:
        random.seed(seed)
        random.shuffle(indexs)
    for n_line,i in enumerate(indexs):
        progress(n_line+1)
        if tok_mode is not None:
            vsrc, _ = tokenizer.tokenize(src[i])
            vtgt, _ = tokenizer.tokenize(tgt[i])
        else:
            vsrc = src[i].split()
            vtgt = tgt[i].split()
        lsrc = ' '.join(vsrc)
        ltgt = ' '.join(vtgt)
        lmax = max(len(vsrc),len(vtgt))
        lmin = min(len(vsrc),len(vtgt))
        pair = lsrc + '\t' + ltgt

        if Equals and lsrc == ltgt:
            if (verbose): sys.stderr.write('{} Equals\n'.format(i))
            nEquals += 1
            continue
        if Min != 0 and lmin < Min:
            if (verbose): sys.stderr.write('{} Min ({})\n'.format(i,lmin))
            nMin += 1
            continue
        if Max != 0 and lmax > Max:
            if (verbose): sys.stderr.write('{} Max ({})\n'.format(i,lmax))
            nMax += 1
            continue
        if Maxw != 0:
            maxw = len(max(max(vsrc,key=len), max(vtgt,key=len)))
            if maxw > Maxw:
                if (verbose): sys.stderr.write('{} Maxw ({})\n'.format(i,maxw))
                nMaxw += 1
                continue
        if Fert != 0:
            if lmin > 0:
                fert = lmax / float(lmin)
                if fert > Fert:
                    if (verbose): sys.stderr.write('{} Fert ({})\n'.format(i,fert))
                    nFert += 1
                    continue
        if Uniq:
            if pair in output:
                if (verbose): sys.stderr.write('{} Uniq\n'.format(i))
                nUniq += 1
                continue
            output.add(pair)

        if tok_mode is not 'space':
            vsrc, _ = tokenizer_space.tokenize(src[i])
            vtgt, _ = tokenizer_space.tokenize(tgt[i])
        fs.write(' '.join(vsrc)+'\n')
        ft.write(' '.join(vtgt)+'\n')
        n_output += 1
    fs.close()
    ft.close()

    sys.stderr.write('(output {} out of {} [{:.2f}%] nEquals={} nMin={} nMax={} nMaxw={} nFert={} nUniq={})\n'.format(n_output,len(src),100*n_output/float(len(src)),nEquals,nMin,nMax,nMaxw,nFert,nUniq))
