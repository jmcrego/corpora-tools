# -*- coding: utf-8 -*-

import sys
from random import shuffle
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
    Fert = 6.0
    Uniq = False
    Equals = False
    tok_mode = None
    seed = None
    fs = None
    ft = None
    tag = 'clean_min{}_max{}_fert{}_uniq{}_equals{}_tok{}'.format(Min,Max,Fert,Uniq,Equals,tok_mode)
    verbose = False
    name = sys.argv.pop(0)
    usage = '''usage: {} -src FILE -tgt FILE [-tag STRING] [-min INT] [-max INT] [-fert FLOAT] [-uniq] [-equals] [-seed INT]
   -src   FILE : input source file
   -tgt   FILE : input target file
   -tag STRING : output files are built adding this prefix to the original file names (default {})

   -tok   MODE : use pyonmttok tokenizer aggressive|conservative|space before statistics computation (default {})
   -min    INT : discard if src/tgt contains less than [min] words (default {})
   -max    INT : discard if src/tgt contains more than [max] words (default {})
   -fert FLOAT : discard if src/tgt is [fert] times bigger than tgt/src (default {})
   -uniq       : discard repeated sentence pairs (default {})
   -equals     : discard if src equals to tgt (default {})

   -seed   INT : seed for random shuffle (default {}). Do not set to avoid shuffling
   -v          : verbose output (default False)
   -h          : this help

   The script neecds pyonmttok installed (pip install OpenNMT-tf)
   Output files are tokenised following opennmt tokenizer 'space' mode
'''.format(name,tag,tok_mode,Min,Max,Fert,Uniq,Equals,seed)
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
        elif tok=="-min" and len(sys.argv):
            Min = int(sys.argv.pop(0))
        elif tok=="-max" and len(sys.argv):
            Max = int(sys.argv.pop(0))
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
        tag = 'clean_min{}_max{}_fert{}_uniq{}_equals{}_tok{}'.format(Min,Max,Fert,Uniq,Equals,tok_mode)


    tokenizer_space = pyonmttok.Tokenizer('space', joiner_annotate=False)
    if tok_mode is not None:
        tokenizer = pyonmttok.Tokenizer(tok_mode, joiner_annotate=False)

    f = open(fs,'r')
    src = [x.rstrip() for x in f]
    f.close()
    sys.stderr.write('Read {}\n'.format(fs))

    f = open(ft,'r')
    tgt = [x.rstrip() for x in f]
    f.close()
    sys.stderr.write('Read {}\n'.format(ft))

    if len(src) != len(tgt):
        sys.stderr.write('error: diff num of sentences in source/target files!\n')
        sys.exit()

    FS = fs.split('/')
    FS[-1] = tag + '.' + FS[-1]    
    fs = open('/'.join(FS),'w')

    FT = ft.split('/')
    FT[-1] = tag + '.' + FT[-1]
    ft = open('/'.join(FT),'w')

    output = set()
    nEquals = 0
    nMin = 0
    nMax = 0
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
        if lmin > 0:
            fert = lmax / float(lmin)
        pair = lsrc + '\t' + ltgt
        if Equals and lsrc == ltgt:
            if (verbose): sys.stderr.write('{} Equals\n'.format(i))
            nEquals += 1
            continue
        if lmin < Min:
            if (verbose): sys.stderr.write('{} Min ({})\n'.format(i,lmin))
            nMin += 1
            continue
        if lmax > Max:
            if (verbose): sys.stderr.write('{} Max ({})\n'.format(i,lmax))
            nMax += 1
            continue
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

    sys.stderr.write('(output {} out of {} [{:.2f}%] nEquals={} nMin={} nMax={} nFert={} nUniq={})\n'.format(n_output,len(src),100*n_output/float(len(src)),nEquals,nMin,nMax,nFert,nUniq))
