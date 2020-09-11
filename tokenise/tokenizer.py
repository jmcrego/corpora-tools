# -*- coding: utf-8 -*-

import os
import sys
import six
import pyonmttok

class tokenizer():
    def __init__(self):
        self.T = None #my tokenizer
        self.tokopts = {
            'mode': "conservative",
            'bpe_model_path': "",
            'bpe_dropout': 0.0,
            'vocabulary_path': "",
            'vocabulary_threshold': 0,
            'sp_model_path': "",
            'sp_nbest_size': 0,
            'sp_alpha': 0.1,
            'joiner': "￭",
            'joiner_annotate': False,
            'joiner_new': False,
            'spacer_annotate': False,
            'spacer_new': False,
            'case_feature': False,
            'case_markup': False,
            'no_substitution': False,
            'preserve_placeholders': False,
            'preserve_segmented_tokens': False,
            'segment_case': False,
            'segment_numbers': False,
            'segment_alphabet_change': False,
            'support_prior_joiners': False,
            'segment_alphabet': []
        }
        self.opt_strings = ['mode','bpe_model_path','vocabulary_path','sp_model_path','joiner']
        self.opt_ints = ['vocabulary_threshold','sp_nbest_size']
        self.opt_floats = ['bpe_dropout','sp_alpha']
        self.opt_lists = ['segment_alphabet']
        self.opt_bools = ['joiner_annotate','joiner_new','spacer_annotate','spacer_new','case_feature','case_markup','no_substitution','preserve_placeholders','preserve_segmented_tokens','segment_case','segment_numbers','segment_alphabet_change','support_prior_joiners']
        
    def build_tokenizer(self):
        #sys.stderr.write("Options = {}\n".format(self.tokopts))
        local_args = {}
        for k, v in six.iteritems(self.tokopts):
            if isinstance(v, six.string_types):
                local_args[k] = v.encode('utf-8')
            else:
                local_args[k] = v
        mode = local_args['mode']
        del local_args['mode']
        self.T = pyonmttok.Tokenizer(mode, **local_args)

    def tokenize_file(self,fin, fout, num_threads):
        if self.T == None:
            self.build_tokenizer()
        self.T.tokenize_file(input_path=fin, output_path=fout, num_threads=num_threads)

    def tokenize_string(self,line):
        if self.T == None:
            self.build_tokenizer()
        line, _ = self.T.tokenize(line)
        return line
        
