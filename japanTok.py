# -*- coding: utf-8 -*-
import MeCab
import sys
import numpy as np

TAG_MAP_DICT = {
    "名詞": "N",
    "名詞-一般": "N.g",
    "名詞-固有名詞": "N.Prop",
    "名詞-固有名詞-一般": "N.Prop.g",
    "名詞-固有名詞-人名": "N.Prop.n",
    "名詞-固有名詞-人名-一般": "N.Prop.n.g",
    "名詞-固有名詞-人名-姓": "N.Prop.n.s",
    "名詞-固有名詞-人名-名": "N.Prop.n.f",
    "名詞-固有名詞-組織": "N.Prop.o",
    "名詞-固有名詞-地域": "N.Prop.p",
    "名詞-固有名詞-地域-一般": "N.Prop.p.g",
    "名詞-固有名詞-地域-国": "N.Prop.p.c",
    "名詞-代名詞": "N.Pron",
    "名詞-代名詞-一般": "N.Pron.g",
    "名詞-代名詞-縮約": "N.Pron.sh",
    "名詞-副詞可能": "N.Adv",
    "名詞-サ変接続": "N.Vs",
    "名詞-形容動詞語幹": "N.Ana",
    "名詞-数": "N.Num",
    "名詞-非自立": "N.bnd",
    "名詞-非自立-一般": "N.bnd.g",
    "名詞-非自立-副詞可能": "N.bnd.Adv",
    "名詞-非自立-助動詞語幹": "N.bnd.Aux",
    "名詞-非自立-形容動詞語幹": "N.bnd.Ana",
    "名詞-特殊-": "N.spec",
    "名詞-特殊-助動詞語幹": "N.spec.Aux",
    "名詞-接尾": "N.Suff",
    "名詞-接尾-一般": "N.Suff.g",
    "名詞-接尾-人名": "N.Suff.n",
    "名詞-接尾-地域": "N.Suff.p",
    "名詞-接尾-サ変接続": "N.Suff.Vs",
    "名詞-接尾-助動詞語幹": "N.Suff.Aux",
    "名詞-接尾-形容動詞語幹": "N.Suff.Ana",
    "名詞-接尾-副詞可能": "N.Suff.Adv",
    "名詞-接尾-助数詞": "N.Suff.msr",
    "名詞-接尾-特殊": "N.Suff.spec",
    "名詞-接続詞的": "N.Conj",
    "名詞-動詞非自立的": "N.V.bnd",
    "名詞-引用文字列": "N.Phr",
    "名詞-ナイ形容詞語幹": "N.nai",
    "接頭詞": "Pref",
    "接頭詞-名詞接続": "Pref.N",
    "接頭詞-動詞接続": "Pref.V",
    "接頭詞-形容詞接続": "Pref.Ai",
    "接頭詞-数接続": "Pref.Num",
    "動詞": "V",
    "動詞-自立": "V.free",
    "動詞-非自立": "V.bnd",
    "動詞-接尾": "V.Suff",
    "形容詞": "Ai",
    "形容詞-自立": "Ai.free",
    "形容詞-非自立": "Ai.bnd",
    "形容詞-接尾": "Ai.Suff",
    "副詞": "Adv",
    "副詞-一般": "Adv.g",
    "副詞-助詞類接続": "Adv.P",
    "連体詞": "Adn",
    "接続詞": "Conj",
    "助詞": "P",
    "助詞-格助詞": "P.c",
    "助詞-格助詞-一般": "P.c.g",
    "助詞-格助詞-引用": "P.c.r",
    "助詞-格助詞-連語": "P.c.Phr",
    "助詞-接続助詞": "P.Conj",
    "助詞-係助詞": "P.bind",
    "助詞-副助詞": "P.Adv",
    "助詞-間投助詞": "P.ind",
    "助詞-並立助詞": "P.coord",
    "助詞-終助詞": "P.fin",
    "助詞-副助詞／並立助詞／終助詞": "P.advcoordfin",
    "助詞-連体化": "P.prenom",
    "助詞-副詞化": "P.advzer",
    "助詞-特殊": "P.spec",
    "助動詞": "Aux",
    "感動詞": "Interj",
    "記号": "Sym",
    "記号-一般": "Sym.g",
    "記号-句点": "Sym.p",
    "記号-読点": "Sym.c",
    "記号-空白": "Sym.w",
    "記号-アルファベット": "Sym.a",
    "記号-括弧開": "Sym.bo",
    "記号-括弧閉": "Sym.bc",
    "その他": "Other",
    "その他-間投": "Other.indir",
    "フィラー": "Fill",
    "非言語音": "Nss",
    "語断片": "Frgm",
    "未知語": "Unknown"
}
    
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
                snt.append(tags[0]+sep+tags[1]+sep+TAG_MAP_DICT[tags[3]]+sep+tags[3])
        if oneline:
            print(' '.join(snt))
        else:
            print('\n'.join(snt) + "\n")

