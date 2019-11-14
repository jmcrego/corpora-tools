# corpora-tools
Cleaner, Tokeniser, POS-tagger for different languages, Fuzzy matcher, TfIdf, Eval

## Cleaner:
```usage: corpus-clean-bitext.py -src FILE -tgt FILE [-tag STRING] [-min INT] [-max INT] [-maxw INT] [-fert FLOAT] [-uniq] [-equals] [-seed INT]
   -src   FILE : input source file
   -tgt   FILE : input target file
   -tag STRING : output files are built adding this prefix to the original file names (default clean_min1_max99_maxw0_fert6.0_uniqFalse_equalsFalse_tokNone)

   -tok   MODE : use pyonmttok tokenizer aggressive|conservative|space before statistics computation (default None)
   -min    INT : discard if src/tgt contains less than [min] words (default 1)
   -max    INT : discard if src/tgt contains more than [max] words (default 99)
   -maxw   INT : discard if src/tgt contains a token with more than [maxw] characters (default 0:not used)
   -fert FLOAT : discard if src/tgt is [fert] times bigger than tgt/src (default 6.0)
   -uniq       : discard repeated sentence pairs (default False)
   -equals     : discard if src equals to tgt (default False)

   -seed   INT : seed for random shuffle (default None). Do not set to avoid shuffling
   -v          : verbose output (default False)
   -h          : this help

   The script needs pyonmttok installed (pip install OpenNMT-tf)
   Output files are tokenised following opennmt tokenizer 'space' mode
```


## Tokeniser:
```
usage: onmt-tokenize.py
   -json       FILE : json file containing tokenization options (mode, vocabulary, ...)
   -yaml       FILE : yaml file containing tokenization options (mode, vocabulary, ...)
   -mode       MODE : tokenization mode: aggressive, conservative [aggressive]
   -bpe        FILE : bpe codes to apply bpe subtokenization (use -bpe_model_path)
   -joiner          : use joiner annotate (use -joiner_annotate))
   -lc              : lowercase all data (use -case_feature)
   -vocabulary FILE : vocabulary file
   -h               : this message
```
## FuzzyMathing
```
fuzzyMatching.py  -mod FILE -trn FILE -tst FILE [-tok FILE] [-nbest INT]
       -mod     FILE : Suffix Array model file
       -trn     FILE : train file
       -tst     FILE : test file
       -tok     FILE : options for tokenizer
       -Nbest    INT : show [INT]-best similar sentences (default 10)
       -minNgram INT : min length for test ngrams (default 2)
       -maxNgram INT : max length for test ngrams (default 4)
       -testSet      : collect similar sentences to the entire test set rather than to each input sentence (default false)
       -sortByEDist  : sort collected sentences by edit distance rather than by ngram overlap counts (default false)
```

## TfIdf
```
tfidf.py -tok FILE -mod FILE ([-trn STRING]+ | -tst FILE [-snt])
       -tok   FILE : options for tokenizer
       -mod   FILE : tfidf model file (to create/save)
       -tst   FILE : file used for inference
       -trn STRING : file:tag used for the given domain
       -max      N : max vocabulary size (default 0: use all)
       -snt        : compute tfidf values for each sentence rather the entire tst file
```
```
idf.py [-data FILE] ( -save FILE | -load FILE )
       -tok  FILE : options for tokenizer
       -data FILE : file used to learn/inference
       -save FILE : save tfidf model after building it with data file      (LEARNING)
       -load FILE : load tfidf model and use it for inference on data file (INFERENCE)
```

## POS-tagger (Japanese)


## Eval:
```
usage: multi-bleu.pl [-lc] REF < HYP
```
```
usage: chrF.py [-h] --ref REF --hyp HYP [--beta FLOAT] [--ngram INT] [--space] [--precision] [--recall]
```
```
python Eval/RIBES.py -z -r REF -c HYP
```
