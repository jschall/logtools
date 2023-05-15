from DFParser import DFParser
from sys import argv
from math import *
import matplotlib.pyplot as plt
from collections import deque
import numpy as np
import re
import scipy.io

def retrieve_timeseries(fname, fields, instance=None):
    f = open(fname,'rb')

    parser = DFParser(f)

    fields = [tuple(x.split('.', 1)) for x in fields]

    ret = tuple([[] for _ in fields])
    while True:
        m = parser.parse_next()
        if m is None:
            break

        for i in range(len(fields)):
            msgname = fields[i][0]
            fieldname = fields[i][1]

            if m.get_type() == msgname and (instance is None or m['Instance'] == instance):
                ret[i].append(m[fieldname])

    f.close()

    return [np.asarray(x) for x in ret]

class TimeSeriesCollector:
    def __init__(self, parser, field):
        p = re.compile(r'^(\w+)(\[([0-9]+)\])?\.(\w+)$')
        m = p.match(field)
        self.msgname, _, self.instance, self.fieldname = m.groups()
        self.instance = int(self.instance) if self.instance is not None else None
        self.data = []
        parser.register_cb(self.process_msg)

    def process_msg(self, m):
        if m.get_type() == self.msgname and (self.instance is None or m['Instance'] == self.instance):
            self.data.append(m[self.fieldname])

f = open(argv[1],'rb')

parser = DFParser(f)
t = TimeSeriesCollector(parser, "BAT[0].TimeUS")
voltr = TimeSeriesCollector(parser, "BAT[0].VoltR")
currtot = TimeSeriesCollector(parser, "BAT[0].CurrTot")
curr = TimeSeriesCollector(parser, "BAT[0].Curr")
volt = TimeSeriesCollector(parser, "BAT[0].Volt")
R = TimeSeriesCollector(parser, "BAT[0].Res")
parser.go()
f.close()

t = np.asarray(t.data)/1e6
voltr = np.asarray(voltr.data)
volt = np.asarray(volt.data)
currtot = np.asarray(currtot.data)
curr = np.asarray(curr.data)
R = np.asarray(R.data)

data = {"t": t, "volt":volt, "voltr":voltr, "currtot":currtot, "curr":curr, "R":R}

scipy.io.savemat("data.mat", data)
