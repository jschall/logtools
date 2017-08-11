from DFParser import DFParser
from sys import argv
from math import *
import matplotlib.pyplot as plt
from collections import deque

def retrieve_timeseries(fname, field):
    f = open(fname,'rb')
    data = f.read()
    f.close()

    parser = DFParser(data)

    msgname,fieldname = tuple(field.split('.', 1))

    ret = []

    while True:
        m = parser.parse_next()
        if m is None:
            break

        if m.get_type() == msgname:
            ret.append(m[fieldname])

    return ret


blanking_time = 2.
freefall_thresh = 3.
trigger = -15.
pre_trigger = 0.01
post_trigger = 0.06

event_length = pre_trigger + post_trigger

blanking_time_us = blanking_time*1e6
pre_trigger_us = pre_trigger*1e6
post_trigger_us = post_trigger*1e6

time_us = retrieve_timeseries(argv[1], "ACC3.TimeUS")
acc = retrieve_timeseries(argv[1], "ACC3.AccZ")

events = []

trigger_us = None

delay_buffer = deque()

for i in range(len(time_us)):
    delay_buffer.append((time_us[i], acc[i]))
    while delay_buffer[0][0] < time_us[i]-pre_trigger_us:
        delay_buffer.popleft()

    if trigger_us is None:
        if acc[i] < trigger and abs(delay_buffer[0][1]) < freefall_thresh:
            trigger_us = time_us[i]
            events.append([((x[0]-trigger_us+pre_trigger_us)*1e-6, x[1]) for x in delay_buffer])

    if trigger_us is not None:
        if time_us[i] > trigger_us+blanking_time_us:
            trigger_us = None
        elif time_us[i] < trigger_us+post_trigger_us:
            events[-1].append(((time_us[i]-trigger_us+pre_trigger_us)*1e-6, acc[i]))

plt.figure(figsize=(9,9), dpi=160)
plt.title(argv[1])
plt.axis([0,event_length,-9.81*16,9.81*16])

for e in events:
    plt.plot(*zip(*e))

with open(argv[2], 'wb') as f:
    plt.savefig(f)
