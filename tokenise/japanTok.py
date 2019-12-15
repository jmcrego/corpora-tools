# -*- coding: utf-8 -*-
import MeCab
import sys
import numpy as np
from collections import defaultdict

TAG_MAP_DICT = defaultdict(lambda: 'UNSEEN')
TAG_MAP_DICT["名詞"] = "N"
TAG_MAP_DICT["名詞-一般"] = "N.g"
TAG_MAP_DICT["名詞-固有名詞"] = "N.Prop"
TAG_MAP_DICT["名詞-固有名詞-一般"] = "N.Prop.g"
TAG_MAP_DICT["名詞-固有名詞-人名"] = "N.Prop.n"
TAG_MAP_DICT["名詞-固有名詞-人名-一般"] = "N.Prop.n.g"
TAG_MAP_DICT["名詞-固有名詞-人名-姓"] = "N.Prop.n.s"
TAG_MAP_DICT["名詞-固有名詞-人名-名"] = "N.Prop.n.f"
TAG_MAP_DICT["名詞-固有名詞-組織"] = "N.Prop.o"
TAG_MAP_DICT["名詞-固有名詞-地域"] = "N.Prop.p"
TAG_MAP_DICT["名詞-固有名詞-地域-一般"] = "N.Prop.p.g"
TAG_MAP_DICT["名詞-固有名詞-地域-国"] = "N.Prop.p.c"
TAG_MAP_DICT["名詞-代名詞"] = "N.Pron"
TAG_MAP_DICT["名詞-代名詞-一般"] = "N.Pron.g"
TAG_MAP_DICT["名詞-代名詞-縮約"] = "N.Pron.sh"
TAG_MAP_DICT["名詞-副詞可能"] = "N.Adv"
TAG_MAP_DICT["名詞-サ変接続"] = "N.Vs"
TAG_MAP_DICT["名詞-形容動詞語幹"] = "N.Ana"
TAG_MAP_DICT["名詞-数"] = "N.Num"
TAG_MAP_DICT["名詞-非自立"] = "N.bnd"
TAG_MAP_DICT["名詞-非自立-一般"] = "N.bnd.g"
TAG_MAP_DICT["名詞-非自立-副詞可能"] = "N.bnd.Adv"
TAG_MAP_DICT["名詞-非自立-助動詞語幹"] = "N.bnd.Aux"
TAG_MAP_DICT["名詞-非自立-形容動詞語幹"] = "N.bnd.Ana"
TAG_MAP_DICT["名詞-特殊-"] = "N.spec"
TAG_MAP_DICT["名詞-特殊-助動詞語幹"] = "N.spec.Aux"
TAG_MAP_DICT["名詞-接尾"] = "N.Suff"
TAG_MAP_DICT["名詞-接尾-一般"] = "N.Suff.g"
TAG_MAP_DICT["名詞-接尾-人名"] = "N.Suff.n"
TAG_MAP_DICT["名詞-接尾-地域"] = "N.Suff.p"
TAG_MAP_DICT["名詞-接尾-サ変接続"] = "N.Suff.Vs"
TAG_MAP_DICT["名詞-接尾-助動詞語幹"] = "N.Suff.Aux"
TAG_MAP_DICT["名詞-接尾-形容動詞語幹"] = "N.Suff.Ana"
TAG_MAP_DICT["名詞-接尾-副詞可能"] = "N.Suff.Adv"
TAG_MAP_DICT["名詞-接尾-助数詞"] = "N.Suff.msr"
TAG_MAP_DICT["名詞-接尾-特殊"] = "N.Suff.spec"
TAG_MAP_DICT["名詞-接続詞的"] = "N.Conj"
TAG_MAP_DICT["名詞-動詞非自立的"] = "N.V.bnd"
TAG_MAP_DICT["名詞-引用文字列"] = "N.Phr"
TAG_MAP_DICT["名詞-ナイ形容詞語幹"] = "N.nai"
TAG_MAP_DICT["接頭詞"] = "Pref"
TAG_MAP_DICT["接頭詞-名詞接続"] = "Pref.N"
TAG_MAP_DICT["接頭詞-動詞接続"] = "Pref.V"
TAG_MAP_DICT["接頭詞-形容詞接続"] = "Pref.Ai"
TAG_MAP_DICT["接頭詞-数接続"] = "Pref.Num"
TAG_MAP_DICT["動詞"] = "V"
TAG_MAP_DICT["動詞-自立"] = "V.free"
TAG_MAP_DICT["動詞-非自立"] = "V.bnd"
TAG_MAP_DICT["動詞-接尾"] = "V.Suff"
TAG_MAP_DICT["形容詞"] = "Ai"
TAG_MAP_DICT["形容詞-自立"] = "Ai.free"
TAG_MAP_DICT["形容詞-非自立"] = "Ai.bnd"
TAG_MAP_DICT["形容詞-接尾"] = "Ai.Suff"
TAG_MAP_DICT["副詞"] = "Adv"
TAG_MAP_DICT["副詞-一般"] = "Adv.g"
TAG_MAP_DICT["副詞-助詞類接続"] = "Adv.P"
TAG_MAP_DICT["連体詞"] = "Adn"
TAG_MAP_DICT["接続詞"] = "Conj"
TAG_MAP_DICT["助詞"] = "P"
TAG_MAP_DICT["助詞-格助詞"] = "P.c"
TAG_MAP_DICT["助詞-格助詞-一般"] = "P.c.g"
TAG_MAP_DICT["助詞-格助詞-引用"] = "P.c.r"
TAG_MAP_DICT["助詞-格助詞-連語"] = "P.c.Phr"
TAG_MAP_DICT["助詞-接続助詞"] = "P.Conj"
TAG_MAP_DICT["助詞-係助詞"] = "P.bind"
TAG_MAP_DICT["助詞-副助詞"] = "P.Adv"
TAG_MAP_DICT["助詞-間投助詞"] = "P.ind"
TAG_MAP_DICT["助詞-並立助詞"] = "P.coord"
TAG_MAP_DICT["助詞-終助詞"] = "P.fin"
TAG_MAP_DICT["助詞-副助詞／並立助詞／終助詞"] = "P.advcoordfin"
TAG_MAP_DICT["助詞-連体化"] = "P.prenom"
TAG_MAP_DICT["助詞-副詞化"] = "P.advzer"
TAG_MAP_DICT["助詞-特殊"] = "P.spec"
TAG_MAP_DICT["助動詞"] = "Aux"
TAG_MAP_DICT["感動詞"] = "Interj"
TAG_MAP_DICT["記号"] = "Sym"
TAG_MAP_DICT["記号-一般"] = "Sym.g"
TAG_MAP_DICT["記号-句点"] = "Sym.p"
TAG_MAP_DICT["記号-読点"] = "Sym.c"
TAG_MAP_DICT["記号-空白"] = "Sym.w"
TAG_MAP_DICT["記号-アルファベット"] = "Sym.a"
TAG_MAP_DICT["記号-括弧開"] = "Sym.bo"
TAG_MAP_DICT["記号-括弧閉"] = "Sym.bc"
TAG_MAP_DICT["その他"] = "Other"
TAG_MAP_DICT["その他-間投"] = "Other.indir"
TAG_MAP_DICT["フィラー"] = "Fill"
TAG_MAP_DICT["非言語音"] = "Nss"
TAG_MAP_DICT["語断片"] = "Frgm"
TAG_MAP_DICT["未知語"] = "Unknown"
    
token = False
parse = False
sep = '❘' #Casseau, U+2700 - U+27BF
oneline = False
usage = """usage: {} < file
   -tok     : do tokenization
   -pos     : do pos tagging
   -oneline : output a single line per sentence (default False)
   -sep CHR : use CHR as wrd/pos separator when -oneline (default '{}')
   -h               : this message

Uses MeCab segmenter/tagger (tagset in https://www.sketchengine.eu/japanese-tagset/)
Input is one sentence per line
Ex: echo "これが私のテスト文です。" | python tokenise/japanTok.py -pos
これ   コレ   名詞-代名詞-一般 名詞-代名詞-一般
が     ガ     助詞-格助詞-一般 助詞-格助詞-一般
私     ワタシ 名詞-代名詞-一般 名詞-代名詞-一般
の     ノ     助詞-連体化      助詞-連体化
テスト テスト 名詞-サ変接続    名詞-サ変接続
文     ブン   名詞-一般        名詞-一般
です   デス   助動詞           助動詞
。     。     記号-句点        記号-句点
          (note the empty line at the end of each sentence)
""".format(sys.argv.pop(0),sep)

while len(sys.argv):
    tok = sys.argv.pop(0)
    if tok=="-tok":
        token = True

    elif tok=="-pos":
        parse = True

    elif tok=="-oneline":
        oneline = True

    elif tok=="-oneline" and len(sys.argv):
        sep = sys.argv.pop(0)
        
    elif tok=="-h":
        sys.stderr.write("{}".format(usage))
        sys.exit()

    else:
        sys.stderr.write('error: unparsed {} option\n'.format(tok))
        sys.stderr.write("{}".format(usage))
        sys.exit()

if token:
    wakati = MeCab.Tagger("-Owakati")
if parse:
    chasen = MeCab.Tagger("-Ochasen")

nline = 0
if not oneline:
    sep = '\t'

for line in sys.stdin:
    nline += 1
    line = line.rstrip()
    if len(line)==0:
        sys.stderr.write('warning: line {} is empty\n'.format(nline))
        print()
        continue

    if token:
        res = wakati.parse(line).split()
        if oneline:
            print(' '.join(res))
        else:
            print('\n'.join(res) + "\n")

    if parse:
        snt = []
        res = chasen.parse(line)
        for idx,r in enumerate(res.split('\n')):
            tags = r.split('\t')
            if len(tags) >=4:
                snt.append(tags[0]+sep+tags[1]+sep+tags[2]+sep+TAG_MAP_DICT[tags[3]])
        if oneline:
            print(' '.join(snt))
        else:
            print('\n'.join(snt) + "\n")

