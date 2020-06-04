# -*- coding: utf-8 -*-

import sys
#import io

def heading(fud,fhyps):
    sys.stdout.write('''<!DOCTYPE html>
<html>
<head>
<meta charset=\"UTF-8\">
<style>
table {
    font-family: arial, sans-serif;
    width: 100%;
    border-collapse: collapse;
}
td, th {
  border: 1px solid #dddddd;
  text-align: left;
  padding: 8px;
}
tr:nth-child(even) {
    background-color: #dddddd;
}
</style>
</head>
<body>
<table>
  
<tr>
\t<th>nSent</th>
''')
    sys.stdout.write('\t<th><font size="2">{}</font>'.format(fud))
    for f in range(len(fhyps)):
        #sys.stdout.write('''<hr><font size="2">{fhyps[f]}</font>''')
        sys.stdout.write('<hr><font size="2">{}</font>'.format(fhyps[f]))
    sys.stdout.write('</th>\n</tr>\n')


def ending():
    sys.stdout.write('''</table>
</body>
</html>
''')


def outline(nsent, ud, hyps):
    sys.stdout.write("<tr>\n\t<td>{}</td>\n\t<td>".format(nsent))
    hyps.insert(0,ud)
    sys.stdout.write('<hr>'.join(hyps))
    sys.stdout.write("</td>\n</tr>\n\n");
    

def main():
    name = sys.argv.pop(0)
    color = "blue"
    onlywithuds = False
    usage = '''usage: {} -ud FILE [-h TAG:FILE]+ [-onlywithuds] [-color COLOR] [-h] > output.html
    -ud       FILE : file with UDs
    -hyp  TAG:FILE : hypotheses file preceded by its tag
    -col     COLOR : color used to highlight UDs (default 'blue')
    -h             : help
    '''.format(name)

    fud = None
    fhyps = []
    while len(sys.argv):
        tok = sys.argv.pop(0)
        if   (tok=="-ud" and len(sys.argv)): fud = sys.argv.pop(0)
        elif (tok=="-hyp" and len(sys.argv)): fhyps.append(sys.argv.pop(0))
        elif (tok=="-col" and len(sys.argv)): color = sys.argv.pop(0)
        elif (tok=="-onlywithuds"): onlywithuds = True
        elif (tok=="-h"):
            sys.stderr.write("{}".format(usage))
            sys.exit()
        else:
            sys.stderr.write('error: unparsed {} option\n'.format(tok))
            sys.stderr.write("{}".format(usage))
            sys.exit()

    if fud is None:
        sys.stderr.write('error: missing -ud option\n')
        sys.stderr.write("{}".format(usage))
        sys.exit()

    if len(fhyps) == 0:
        sys.stderr.write('error: missing -hyp option\n')
        sys.stderr.write("{}".format(usage))
        sys.exit()

    UD = []
    with open(fud) as f:
        for line in f:
            line = line.strip()
            UD.append(line)

    HYPS = []
    tags = []
    for i in range(len(fhyps)):
        t,f = fhyps[i].split(':')
        tags.append('<font color = "red">'+t+':</font>')
        fhyps[i] = f
        
    for fhyp in fhyps:
        HYP = []
        with open(fhyp) as f:
            for line in f:
                line = line.strip()
                HYP.append(line)
        HYPS.append(HYP)
        if len(HYP) != len(UD):
            sys.stderr.write('error: read {} sentences instead of {} in {}'.format(len(HYP),len(UD),fhyp))
            sys.exit()
        sys.stderr.write('read {} with {} sentences\n'.format(fhyp,len(HYP)))
    
    sys.stderr.write('Processing...\n')

    heading(fud,fhyps)
    for nsent in range(len(UD)):
        lud = UD[nsent]
        if lud == '':
            if onlywithuds:
                continue
            curr_UDs = []
        else:
            curr_UDs = lud.split(' # ')
        #sys.stderr.write('curr_UDs = {}\n'.format(curr_UDs))
        lhyps = []
        for h in range(len(HYPS)):
            curr_hyp = tags[h]+' '+HYPS[h][nsent]+' '
            done = []
            for curr_UD in curr_UDs:
                if curr_UD in done:
                    continue
                done.append(curr_UD)
                #sys.stderr.write('curr_UD={}'.format(curr_UD))
                curr_hyp = curr_hyp.replace(' '+curr_UD+' ', ' <font color="{}">'.format(color)+curr_UD+'</font> ')
            lhyps.append(curr_hyp)
        for u in range(len(curr_UDs)):
            #sys.stderr.write('curr_UD={}\n'.format(curr_UDs[u]))
            curr_UDs[u] = '<font color="{}">'.format(color)+curr_UDs[u]+'</font>'
        outline(nsent+1,'<font color="red">UDs</font>: '+' # '.join(curr_UDs),lhyps)
    ending()
    sys.stderr.write('Done!\n')



if __name__ == "__main__":
    main()
