#!/bin/bash

install_treetagger(){
    #follow instructions (https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/)
    wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/tree-tagger-linux-3.2.2.tar.gz
    wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/tagger-scripts.tar.gz
    wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/install-tagger.sh
    #parameters
    https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/catalan.par.gz
    wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/english.par.gz
    wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/french.par.gz
    wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/german.par.gz
    wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/spanish.par.gz
    
    sh install-tagger.sh
}

#install_treetagger (saves intstallation dir of treetagger in file: ~/.config/treetagger_wrapper.cfg)
#wrapper installed in: /export/home/crego/anaconda3/envs/venv/lib/python2.7/site-packages/treetaggerwrapper.py
pip3 install treetaggerwrapper #or pip3 install --user treetaggerwrapper
#read https://treetaggerwrapper.readthedocs.io/en/latest/

