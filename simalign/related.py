#import sys
#import copy
#import codecs
#import opennmt
import logging
#import argparse
#import pyonmttok
#import numpy as np
import edit_distance
#import tensorflow as tf

class related():
    def __init__(self, l1, l2):
        ### l1 and l2 are lists of objects than can be compared
        ### initially all non-related (0) 
        self.L1 = [0] * len(l1) 
        self.L2 = [0] * len(l2)
        if len(l1) == 0 or len(l2) == 0  or (len(l1) == 1 and len(l1[0]) == 0) or (len(l2) == 1 and len(l2[0]) == 0):
            return
        self.sm = edit_distance.SequenceMatcher(a=[s.casefold() for s in l1], b=[s.casefold() for s in l2], action_function=edit_distance.highest_match_action)
        for (code, b1, e1, b2, e2) in self.sm.get_opcodes():
            if code == 'equal': ### keep words
                self.L1[b1] = 1
                self.L2[b2] = 1

    def first(self):
        return self.L1

    def second(self):
        return self.L2

    def ratio(self):
        return self.sm.ratio()

    def distance(self):
        return self.sm.distance()
    
