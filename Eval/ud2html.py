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
    print '''</th>
</tr>
'''


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
    usage = '''usage: {} -ud FILE [-h FILE]+ [-color COLOR] [-h] > output.html
    -ud   FILE : file with UDs
    -hyp  FILE : hypotheses file
    -col COLOR : color used to highlight UDs (default 'blue')
    -h         : help
    '''.format(name)

    fud = None
    fhyps = []
    while len(sys.argv):
        tok = sys.argv.pop(0)
        if   (tok=="-ud" and len(sys.argv)): fud = sys.argv.pop(0)
        elif (tok=="-hyp" and len(sys.argv)): fhyps.append(sys.argv.pop(0))
        elif (tok=="-col" and len(sys.argv)): color = sys.argv.pop(0)
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
        curr_UDs = lud.split(' # ')
        lhyps = []
        for h in range(len(HYPS)):
            lhyps.append(' '+HYPS[h][nsent]+' ')
            for curr_UD in curr_UDs:
                #print('curr_UD={}'.format(curr_UD))
                lhyps[-1] = lhyps[-1].replace(' '+curr_UD+' ', ' <font color="{}">'.format(color)+curr_UD+'</font> ')
        outline(nsent+1,lud,lhyps)
    ending()
    sys.stderr.write('Done!\n')



if __name__ == "__main__":
    main()
