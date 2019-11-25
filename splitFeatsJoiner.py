# -*- coding: utf-8 -*-
import sys

if __name__ == '__main__':

    f1 = None
    f2 = None
    tok_f1 = None
    joiner = '￭'
    verbose = False
    name = sys.argv.pop(0)
    usage = '''usage: {} -f1 FILE -f2 FILE -tok_f1 FILE [-joiner STRING] [-v] [-h]
    -f1       FILE : file with original word features
    -f2       FILE : file with additional word features (same num of tokens than f1)
    -tok_f1   FILE : f1 after tokenization wit joiner (parallel to f1)
    -joiner STRING : joiner (default {})
    -v             : verbose output (default False)
    -h             : this help
This scripts outputs tok_f2. It contains the same features than f2 with some of its tokens repeated to match splitted (segmented) tokens in tok_f1 regarding f1.
Example:
f1:     ['this', 'is', 'un', 'example'     , '.']
f2:     ['S'   , 'S' , 'S' , 'R'           , 'S']
tok_f1: ['this', 'is', 'un', 'exa', '￭mple', '.']
out:    ['S'   , 'S' , 'S' , 'R'  , 'R'    , 'S']
'''.format(name,joiner)

    while len(sys.argv):
        tok = sys.argv.pop(0)
        if tok=="-h":
            sys.stderr.write("{}".format(usage))
            sys.exit()
        elif tok=="-v":
            verbose = True
        elif tok=="-f1" and len(sys.argv):
            f1 = sys.argv.pop(0)
        elif tok=="-f2" and len(sys.argv):
            f2 = sys.argv.pop(0)
        elif tok=="-tok_f1" and len(sys.argv):
            tok_f1 = sys.argv.pop(0)
        else:
            sys.stderr.write('error: unparsed {} option\n'.format(tok))
            sys.stderr.write("{}".format(usage))
            sys.exit()

    if f1 is None or f2 is None or tok_f1 is None:
        sys.stderr.write('error: missing file options\n')
        sys.stderr.write("{}".format(usage))
        sys.exit()

    with open(f1) as fd_f1, open(f2) as fd_f2, open(tok_f1) as fd_tok_f1:
        nline = 0
        for f1, f2, tok_f1 in zip(fd_f1, fd_f2, fd_tok_f1):
            nline += 1
            f1 = f1.split()
            f2 = f2.split()
            tok_f1 = tok_f1.split()

            if len(f1) != len(f2):
                sys.stderr.write('error: diff num of tokens between f1/f2 in line: {}\n{}\n{}\n{}'.format(nline,f1,f2,tok_f1))
                sys.exit()
                
            if len(tok_f1) < len(f1):
                sys.stderr.write('error: diff tok_f1 cannot be lower than f1 in line: {}\n{}\n{}\n{}'.format(nline,f1,f2,tok_f1))
                sys.exit()

            if verbose:
                print('F1: '+' '.join(["{}:{}".format(i,x) for i,x in enumerate(f1)]))
                print('F2: '+' '.join(["{}:{}".format(i,x) for i,x in enumerate(f2)]))
                print('TOK_F1: '+' '.join(["{}:{}".format(i,x) for i,x in enumerate(tok_f1)]))

            tok_f2 = []
            prev_end_joiner = False
            isrc = -1
            for i_tok_f1 in range(len(tok_f1)):
                curr_beg_joiner = True if tok_f1[i_tok_f1].startswith(joiner) else False
                curr_end_joiner = True if tok_f1[i_tok_f1].endswith(joiner) else False

                if not curr_beg_joiner and not prev_end_joiner: ### new word
                    isrc += 1
                    if verbose: print('new word {}'.format(tok_f1[i_tok_f1]))
                else:
                    if verbose: print('continuation {}'.format(tok_f1[i_tok_f1]))

                if verbose: print("{}:{}:{}".format(isrc,i_tok_f1,f2[isrc]))

                if isrc >= len(f2):
                    sys.stderr.write('error: bad number of tokens in line: {}\n{}\n{}\n{}'.format(nline,f1,f2,tok_f1))
                    sys.exit()

                tok_f2.append(f2[isrc])
                prev_end_joiner = curr_end_joiner

            if len(tok_f2) != len(tok_f1):
                sys.stderr.write('error: unmatched number of tokens in line: {}\n{}\n{}\n{}'.format(nline,f1,f2,tok_f1))
                sys.exit()

            print(' '.join(tok_f2))

