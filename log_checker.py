#!/usr/bin/env python
from DFParser import DFParser
from sys import argv

f = open(argv[1],'rb')
data = f.read()
f.close()

parser = DFParser(data)
first_time = None
last_time = 0

while True:
    m = parser.parse_next()
    if m is None:
        break

    time_field = 'T' if m.get_type() == 'GPS' else 'TimeMS'
    try:
        if first_time is None:
            first_time = m[time_field]
            print "log begins at time %f sec" % (first_time*1.0e-3)

        if m[time_field]-last_time > 50:
            print "%f sec of log data missing at time %f sec" % ((m[time_field]-last_time)*1.0e-3, last_time*1.0e-3)

        last_time = m[time_field]
    except:
        pass
