#!/usr/bin/env python
from DFParser import DFParser
import sys
from math import *
import re
from scipy.signal import welch
import matplotlib.pyplot as plt
import json
from multiprocessing import Pool
from cStringIO import StringIO
import argparse

f = open(sys.argv[1],'rb')
outf = open(sys.argv[2],'wb')
parser = DFParser(f)

fields = [0,0,0,0,0,0,0,0,0,0,0,0]

while True:
    m = parser.parse_next()
    if m is None:
        break
    
    if m.get_type() == "SPDV":
        fields[m['Idx']+1] = m['V']
        fields[m['Idx']+5] = m['Spd']
    elif m.get_type() == "IMT":
        fields[0] = m['TimeUS']*1e-6
        fields[9] = m['DelAX']/m['DelaT']
        fields[10] = m['DelAY']/m['DelaT']
        fields[11] = m['DelAZ']/m['DelaT']
        outf.write(','.join(map(str, fields))+'\n')

f.close()
outf.close()
