#!/usr/bin/env python
from DFParser import DFParser
import matplotlib.pyplot as plt
from scipy import signal
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('in_log', nargs=1)
parser.add_argument('out_log', nargs=1)
parser.add_argument('begin_time', nargs=1)
parser.add_argument('end_time', nargs=1)
args = parser.parse_args()

in_f = open(args.in_log[0],'rb')

parser = DFParser(in_f)

begin = float(args.begin_time[0])
end = float(args.end_time[0])

buf = ''

in_interval = False

while True:
    m = parser.parse_next()
    if m is None:
        break

    if 'TimeUS' in m._fieldnames:
        in_interval = m['TimeUS'] >= begin and m['TimeUS'] <= end
        if m['TimeUS'] > end:
            break

    if m.get_type() == 'PARM' or m.get_type() == 'FMT' or in_interval:
        buf += m.get_msgbuf()

in_f.close()

f = open(args.out_log[0],'wb')
f.write(buf)
f.close()


