import sys

for line in sys.stdin:
    toks = line.rstrip().split()
    print(' '.join(['1.000000' for t in toks]))
