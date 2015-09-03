#!/usr/bin/env python
from DFParser import DFParser
from sys import argv

f = open(argv[1],'rb')
data = f.read()
f.close()

parser = DFParser(data)

while True:
    if parser.parse_next() is None:
        break

tot = 0
gmbtot = 0
imutot = 0
ekftot = 0
magtot = 0

msg_usage = []
for key,qty in parser.msg_count.iteritems():
    if qty > 0:
        name = parser.formats[key].name
        msg_len = parser.formats[key].len
        msg_usage.append((name,msg_len*qty))

        tot += msg_len*qty
        if name.startswith('GMB'):
            gmbtot += msg_len*qty
        elif name.startswith('IMU'):
            imutot += msg_len*qty
        elif name.startswith('EKF'):
            ekftot += msg_len*qty
        elif name.startswith('MAG'):
            magtot += msg_len*qty

msg_usage.append(("_TOTAL", tot))
msg_usage.append(("_TOTAL_GMB", gmbtot))
msg_usage.append(("_TOTAL_IMU", imutot))
msg_usage.append(("_TOTAL_EKF", ekftot))
msg_usage.append(("_TOTAL_MAG", magtot))



msg_usage.sort(key=lambda x:x[1], reverse=True)

for k,v in msg_usage:
    print k,v,"%.1f%%" % ((100.*v)/tot)
