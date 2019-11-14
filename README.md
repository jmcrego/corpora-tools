# corpora-tools
Cleaner, Tokeniser, POS-tagger for different languages, Fuzzy matcher, FfIdf, Eval

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

## POS-tagger

## FuzzyMathing

## TfIdf

## Eval:
* perl Eval/multi-bleu.perl REF < HYP
* python Eval/chrF.py  -r  REF < HYP
* python Eval/RIBES.py -z -r REF -c HYP
