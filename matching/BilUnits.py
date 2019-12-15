# -*- coding: utf-8 -*-
import sys

class BilUnits(object):

    def __init__(self, vsrc, vtgt, vali, verbose, nline):
        self.verbose = verbose
        if self.verbose and False:
            print('N: {}'.format(nline))
            print('SRC: {}'.format(' '.join(vsrc)))
            print('TGT: {}'.format(' '.join(vtgt)))
            print('ALI: {}'.format(' '.join(vali)))

        self.src = vsrc
        self.tgt = vtgt
        self.s2t = [set() for x in range(len(self.src))]
        self.t2s = [set() for x in range(len(self.tgt))]
        for a in vali:
            (s,t) = map(int,a.split('-'))
            if s >= len(self.src) or t >= len(self.tgt):
                sys.stderr.write('error: s={} or t={} out of bounds (max_s={} max_t={})\n'.format(s,t,len(self.src)-1,len(self.tgt)-1))
                sys.exit()
            self.s2t[s].add(t)
            self.t2s[t].add(s)
            

    def tuples_of_src_sequence(self, src_beg, src_end):
        s_used = []
        t_used = []
        tuples = []
        for s in range(src_beg,src_end):
            if s in s_used: ### word s already found in another group
                continue
            tuple_s, tuple_t = self.tuple_of(s, consecutive_in_src=True)
            for sg in tuple_s:
                if sg in s_used:
                    sys.stderr.write('error: s={} in several units\n'.format(sg))
                    sys.exit()
                if sg < src_beg or sg >= src_end:
                    return []
                s_used.append(sg)
            for tg in tuple_t:
                if tg in t_used:
                    sys.stderr.write('error: t={} in several units\n'.format(tg))
                    sys.exit()
                t_used.append(tg)
            tuples.append([tuple_s,tuple_t])

        if self.verbose:
            for u in tuples:
                ts = u[0]
                tt = u[1]
                print("{} >>> {}".format(' '.join(["{}:{}".format(x,self.src[x]) for x in u[0]]), ' '.join(["{}:{}".format(x,self.tgt[x]) for x in u[1]])))

        return tuples


    def Unfold_tgt(self, consecutive_in_tgt=False): ############################################################################
        self.aux = self.src
        self.src = self.tgt
        self.tgt = self.aux
        self.aux = self.s2t
        self.s2t = self.t2s
        self.t2s = self.aux
        self.Unfold_src(consecutive_in_tgt)
        aux = self.tuples
        self.tuples = []
        for u in aux:
            self.tuples.append([u[1],u[0]])
        self.aux = self.src
        self.src = self.tgt
        self.tgt = self.aux
        self.aux = self.s2t
        self.s2t = self.t2s
        self.t2s = self.aux


    def Unfold_src(self, consecutive_in_src=False): ############################################################################
        self.tuples = []
        s_used = [] ### indicates if src[s] is already used in some tuple
        t_used = [] ### indicates if tgt[t] is already used in some tuple
        for s in range(len(self.src)):
            if s in s_used: ### word s already found in another group
                continue
            tuple_s, tuple_t = self.tuple_of(s, consecutive_in_src)
            for sg in tuple_s:
                if sg in s_used:
                    sys.stderr.write('error: s={} in several units\n'.format(sg))
                    sys.exit()
                s_used.append(sg)
            for tg in tuple_t:
                if tg in t_used:
                    sys.stderr.write('error: t={} in several units\n'.format(tg))
                    sys.exit()
                t_used.append(tg)
            self.tuples.append([tuple_s,tuple_t])


        for t in range(len(self.tgt)): ### t's that are not present on any tuple
            if t not in t_used:
                tuple_s = []
                tuple_t = [t]
                self.tuples.append([tuple_s,tuple_t])

        if self.verbose:
            for u in self.tuples:
                print("UNFOLD [{} >>> {}]".format(' '.join([str(x)+':'+self.src[x] for x in u[0]]), ' '.join([str(x)+':'+self.tgt[x] for x in u[1]])))


    def tuple_of(self, s, consecutive_in_src): ############################################################################
        tuple_s = [s]
        tuple_t = []
        find_s_or_t = 1 #1 means find t's aligned to tuple_s, -1 means find s's aligned to tuple_t
        while True:

            if find_s_or_t > 0: #find t's aligned to tuple_s
                tuple_from = tuple_s
                tuple_to = tuple_t
                from2to = self.s2t
                consecutive_in_from = consecutive_in_src
            else: #find s's aligned to tuple_t
                tuple_from = tuple_t
                tuple_to = tuple_s
                from2to = self.t2s
                consecutive_in_from = False

            new_tuple_to = self.spill(tuple_from,consecutive_in_from,from2to)

            if len(new_tuple_to) == len(tuple_to):
                stop = True
            else:
                stop = False            

            if find_s_or_t > 0: 
                tuple_t = new_tuple_to
            else: #find s's aligned to tuple_t
                tuple_s = new_tuple_to

            if stop:
                return tuple_s, tuple_t

            find_s_or_t *= -1

    def spill(self, tuple_x, consecutive_in_x, x2y): ############################################################################
        if consecutive_in_x:
            tuple_x.sort(key=int)
            range_x = range(tuple_x[0], tuple_x[-1]+1)
        else:
            range_x = tuple_x

        tuple_y = []
        for x in range_x:
            for y in x2y[x]:
                if y not in tuple_y:
                    tuple_y.append(y)
        return tuple_y

    def s_aligned_to(self,src_beg, src_end):
        tgt_set = []
        for s in range(src_beg,src_end):
            for t in self.s2t[s]:
                if t not in tgt_set:
                    tgt_set.append(t)

        for t in tgt_set:
            for s in self.t2s[t]:
                if s < src_beg or s >= src_end:
                    return []

        tgt_set.sort(key=int)
        if self.verbose:
            sys.stdout.write("tgt set: {}\n".format(' '.join(["{}:{}".format(x,self.tgt[x]) for x in tgt_set])))            
            
        return tgt_set
