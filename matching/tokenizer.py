# -*- coding: utf-8 -*-

import os
import sys
import six
import logging
import pyonmttok

def build_tokenizer(tokopts):
    logging.info("Options = {}".format(tokopts))
    #sys.stderr.write("Options = {}\n".format(self.tokopts))
    local_args = {}
    for k, v in six.iteritems(tokopts):
        if isinstance(v, six.string_types):
            local_args[k] = v.encode('utf-8')
        else:
            local_args[k] = v
    mode = local_args['mode']
    del local_args['mode']
    return pyonmttok.Tokenizer(mode, **local_args)
    
