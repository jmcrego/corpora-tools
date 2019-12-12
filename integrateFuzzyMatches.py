# -*- coding: utf-8 -*-
import sys
import edit_distance

class FMI(object):

    def __init__(self, tst, src, tgt, ali, repair, repair2, hideR, subseq, verbose):
        self.verbose = verbose
        self.repair = repair
        self.repair2 = repair2
        self.hideR = hideR
        self.subseq = subseq
        self.tst = tst
        self.src = src
        self.tgt = tgt
        self.s2t = [set() for x in range(len(self.src))]
        self.t2s = [set() for x in range(len(self.tgt))]
        self.s2t_minmax = [{'min': -1, 'max': -1} for x in range(len(self.src))]
        self.t2s_minmax = [{'min': -1, 'max': -1} for x in range(len(self.tgt))]
        for a in ali:
            (s,t) = map(int,a.split('-'))
            self.s2t[s].add(t)
            self.t2s[t].add(s)
            if self.s2t_minmax[s]['min'] == -1 or self.s2t_minmax[s]['min'] > t: 
                self.s2t_minmax[s]['min'] = t
            if self.s2t_minmax[s]['max'] == -1 or self.s2t_minmax[s]['max'] < t: 
                self.s2t_minmax[s]['max'] = t
            if self.t2s_minmax[t]['min'] == -1 or self.t2s_minmax[t]['min'] > s: 
                self.t2s_minmax[t]['min'] = s
            if self.t2s_minmax[t]['max'] == -1 or self.t2s_minmax[t]['max'] < s: 
                self.t2s_minmax[t]['max'] = s

    def Unfold(self):

        self.tuples = []
        s_used = [] ### indicates if src[s] is already used in some tuple
        for s in range(len(self.src)):
            if s in s_used: ### word s already found in another group
                continue

            tuple_s, tuple_t = self.tuple_of(s)
            if len(tuple_t) == 0:
                continue

            all_s_present_in_test = True
            for sg in tuple_s:
                if self.src2tst[sg] == False:
                    all_s_present_in_test = False
                s_used.append(sg)

            if all_s_present_in_test: #all s in tuple_s are aligned to test (present in fuzzy match)
                self.tuples.append([tuple_s,tuple_t])
                if self.verbose:
                    print("SRC2TGT [{} > {}]".format(' '.join([str(x)+':'+self.src[x] for x in tuple_s]), ' '.join([str(x)+':'+self.tgt[x] for x in tuple_t])))
        return

    def tuple_of(self, s):
        tuple_s = [s]
        tuple_t = []
        tuple_s_minmax = {'min':s, 'max':s}

        while True:

            do_continue = False                
#            for s in tuple_s:
            for s in range(tuple_s_minmax['min'], tuple_s_minmax['max']+1):
                for t in self.s2t[s]:
                    if t not in tuple_t:
                        tuple_t.append(t)
                        do_continue = True
            if not do_continue:
                break

            do_continue = False
            for t in tuple_t:
                for s in range(self.t2s_minmax[t]['min'],self.t2s_minmax[t]['max']+1):
 #                   if s>-1 and s not in tuple_s:
 #                       tuple_s.append(s)
                    if s < tuple_s_minmax['min']:
                        tutple_s_minmax['min'] = s
                        do_continue = True
                    elif s > tuple_s_minmax['max']:
                        tuple_s_minmax['max'] = s
                        do_continue = True
            if not do_continue:
                break

        tuple_s = [x for x in range(tuple_s_minmax['min'], tuple_s_minmax['max']+1)]
        tuple_s.sort(key=int)
        tuple_t.sort(key=int)
        return tuple_s, tuple_t

    def EDAlignment(self):
        self.tst2src = [-1] * len(self.tst) ### this vector points to the corresponsing src word for each tst word (or -1 if there is no correspondence)
        self.src2tst = [-1] * len(self.src)
        sm =  edit_distance.SequenceMatcher(self.tst, self.src)
        blocks = sm.get_matching_blocks()
        for block in blocks:
            self.tst2src[block[0]] = block[1]
            self.src2tst[block[1]] = block[0]

        if self.verbose:
            for x in range(len(self.tst2src)):
                if self.tst2src[x] != -1:
                    print('TST2SRC [{}:{} {}:{}]'.format(x,self.tst[x],self.tst2src[x],self.src[self.tst2src[x]]))

        return

    def RepairSource(self):
        containsFM = True
        seq = []
        for x in range(len(self.tst)):
            if not self.repair2 or self.tst2src[x]<0:
                seq.append([self.tst[x],'S'])
            else:
                seq.append([self.tst[x],'C'])

        seq.append(['@@@', 'R'])

        for t in range(len(self.tgt)):
            ### check if x is linked to a src (tgt2src) that is link to a tst (src2tst) 
            ### if so, use 'T' otherwise use 'R'
            tag = 'R' ### not linked to tst sentence
            if self.t2s_minmax[t]['min'] > -1:
                for s in range(self.t2s_minmax[t]['min'], self.t2s_minmax[t]['max']+1):
                    if self.src2tst[s] > -1:
                        tag = 'T' ### linked to tst sentence

            if tag == 'T':
                seq.append([self.tgt[t],tag])

            else: ### tag is 'R'
                if not self.hideR:
                    seq.append([self.tgt[t],tag])
                else:
                    if len(seq)==0 or seq[-1][1] != 'R':
                        seq.append(['@@@','R'])
                
        if self.hideR and seq[-1][1] == 'R': #### delete last token if it is 'R'
            seq.pop()

        return containsFM, seq

            
    def RewriteSource(self):
        self.EDAlignment()
        self.Unfold()
        if self.repair:
            containsFM, seq = self.RepairSource()
            return containsFM, seq

        containsFM = False
        seq = []
        for x in range(len(self.tst)):

            s = self.tst2src[x]
            if s == -1: ### not present in a fuzzy match
                seq.append([self.tst[x],'S'])
                continue

            ### find if s belongs to a tuple
            gs = []
            gt = []
            for tuple in self.tuples:
                if s in tuple[0]: 
                    gs = tuple[0]
                    gt = tuple[1]
            if len(gs) == 0 or len(gt) == 0: ### does not belong to a tuple or there is no tgt word
                seq.append([self.tst[x],'S'])
                continue
            
            seq.append([self.tst[x],'R']) ### within a tuple and with a translation
            containsFM = True

            if gs[-1] != s: ### s belongs to a tuple but it is not the last of the tuple
                continue

            ### if s is the last of its tuple 
            ### now i print all tgt words of the tuple
            ### if all s words in tuple are aligned to any tst word
            all_s_in_tuple_are_aligned_to_tst = True
            for s2 in gs:
                if self.src2tst[s2] == -1:
                    all_s_in_tuple_are_aligned_to_tst = False
                    break

            if not all_s_in_tuple_are_aligned_to_tst:
                continue
            
            for t in gt: 
                seq.append([self.tgt[t],'T']) ### a translation

        return containsFM, seq

            
if __name__ == '__main__':

    name = sys.argv.pop(0)
    usage = '''{} -sim FILE -tst FILE -src FILE -tgt FILE -ali FILE -out FILE [-sep CHAR] [-v]
    -sim FILE : FUZZYMATCHES file produced by Systran's FuzzyMatch-cli (FuzzyMatch-cli -a index -c SOURCE / FuzzyMatch-cli -a match -i SOURCE.fmi -f 0.6 -n 1 -P < TEST > FUZZYMATCHES)
    -col  INT : column in sim FILE where the training sentence with the match can be found (first column is 0)
    -tst FILE : TEST file (for which FuzzyMatch-cli has found fuzzy matches)
    -src FILE : SOURCE file (indexed by FuzzyMatch-cli)
    -tgt FILE : target file (parallel to SOURCE)
    -ali FILE : alignments file (parallel to SOURCE)
    -out FILE : output files out.f1 .f2 will be created
    -sep CHAR : feature separator (default \'￨\')
    -repair   : perform fuzzy-match repair (NFR) rather than integration
    -repair2  : perform fuzzy-match repair on both sides (activates -repair)
    -hideR    : hide \'R\' words
    -subseq   : subseq-match mode (default fuzzy-match mode)
    -v        : verbose output

This scripts needs edit_distance (pip install edit_distance)
This scripts works with the fuzzymatch output produced by Systran's FuzzyMatch-cli
'''.format(name)

    fsim = None
    ftst = None
    fsrc = None
    ftgt = None
    fali = None
    fout = None
    col = None
    sep = '￨'
    repair = False
    repair2 = False
    hideR = False
    subseq = False
    verbose = False
    while len(sys.argv):
        tok = sys.argv.pop(0)
        if   (tok=="-sim" and len(sys.argv)): fsim = sys.argv.pop(0)
        elif (tok=="-tst" and len(sys.argv)): ftst = sys.argv.pop(0)
        elif (tok=="-src" and len(sys.argv)): fsrc = sys.argv.pop(0)
        elif (tok=="-tgt" and len(sys.argv)): ftgt = sys.argv.pop(0)
        elif (tok=="-ali" and len(sys.argv)): fali = sys.argv.pop(0)
        elif (tok=="-out" and len(sys.argv)): fout = sys.argv.pop(0)
        elif (tok=="-sep" and len(sys.argv)): sep = sys.argv.pop(0)
        elif (tok=="-col" and len(sys.argv)): col = int(sys.argv.pop(0))
        elif (tok=="-repair"): repair = True
        elif (tok=="-repair2"): 
            repair2 = True
            repair = True
        elif (tok=="-subseq"): subseq = True
        elif (tok=="-hideR"): hideR = True
        elif (tok=="-v"): verbose = True
        elif (tok=="-h"):
            sys.stderr.write("{}".format(usage))
            sys.exit()
        else:
            sys.stderr.write('error: unparsed {} option\n'.format(tok))
            sys.stderr.write("{}".format(usage))
            sys.exit()

    if fsim is None or ftst is None or fsrc is None or ftgt is None or fali is None or fout is None:
        sys.stderr.write("error: missing file option\n")
        sys.stderr.write("{}".format(usage))
        sys.exit()

    if col is None:
        sys.stderr.write("error: missing col option\n")
        sys.stderr.write("{}".format(usage))
        sys.exit()

    sim = [line.rstrip('\n').split() for line in open(fsim)]
    sys.stderr.write('Read fsim={} [{}]\n'.format(fsim,len(sim)))
    tst = [line.rstrip('\n').split() for line in open(ftst)]
    sys.stderr.write('Read ftst={} [{}]\n'.format(ftst,len(tst)))
    if len(sim) != len(tst):
        sys.stderr.write("error: diff number of lines in input sim/tst files\n")
        sys.exit()

    src = [line.rstrip('\n').split() for line in open(fsrc)]
    sys.stderr.write('Read fsrc={} [{}]\n'.format(fsrc,len(src)))
    tgt = [line.rstrip('\n').split() for line in open(ftgt)]
    sys.stderr.write('Read ftgt={} [{}]\n'.format(ftgt,len(tgt)))
    ali = [line.rstrip('\n').split() for line in open(fali)]
    sys.stderr.write('Read fali={} [{}]\n'.format(fali,len(ali)))
    if len(src) != len(tgt) or len(src) != len(ali):
        sys.stderr.write("error: diff number of lines in input src/tgt/ali files\n")
        sys.exit()

    f1 = open(fout+'.f1','w')
    f2 = open(fout+'.f2','w')

    for n,line in enumerate(sim):
        if verbose:
            print('n={}'.format(n))

        if len(line) == 0: ### empty line???
            if verbose:
                print('')
            f1.write('\n')
            f2.write('\n')
            continue

        score = float(line[0])
        nsim = int(line[col])-1
        if n >= len(src) or nsim >= len(src):
            sys.stderr.write("error: index out of bounds n={} nsim={}\n".format(n+1,nsim))
            sys.exit()

        if verbose:
            print('nsim={}'.format(nsim))
            print('score={}'.format(score))
            print('TST[{}]'.format(n)+'\t'+' '.join(tst[n]))
            print('SRC[{}]'.format(nsim)+'\t'+' '.join(src[nsim]))
            print('TGT[{}]'.format(nsim)+'\t'+' '.join(tgt[nsim]))
            print('ALI[{}]'.format(nsim)+'\t'+' '.join(ali[nsim]))

        F = FMI(tst[n],src[nsim],tgt[nsim],ali[nsim],repair,repair2,hideR,subseq,verbose)
        containsFM, source = F.RewriteSource() #tst[n],src[nsim],tgt[nsim],tst2src,src2tst,tuples,verbose)
        if containsFM:
            S1 = []
            S2 = []
            for [s1, s2] in source:
                S1.append(s1)
                S2.append(s2)
            f1.write(' '.join(S1)+'\n')
            f2.write(' '.join(S2)+'\n')
            if verbose:
                print(' '.join(S1))
                print(' '.join(S2))
        else:
            f1.write('\n')
            f2.write('\n')
            if verbose:
                print('')

    f1.close()
    f2.close()

