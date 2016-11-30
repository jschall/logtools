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

def get_versions(fn):
    re_apmver = re.compile(r"^APM:Copter.+\(([0-9a-fA-F]{8})\)$")
    re_px4nuttxver = re.compile(r"^PX4: ([0-9a-fA-F]{8}) NuttX: ([0-9a-fA-F]{8})$")

    apmver = None
    px4ver = None
    nuttxver = None
    ftsver = None

    f = open(fn,'rb')
    parser = DFParser(f.read())
    f.close()

    while True:
        m = parser.parse_next()
        if m is None:
            break

        if m.get_type() == 'MSG':
            mobj = re_apmver.match(m['Message'])
            if mobj is not None:
                apmver = mobj.group(1)

            mobj = re_px4nuttxver.match(m['Message'])
            if mobj is not None:
                px4ver = mobj.group(1)
                nuttxver = mobj.group(2)

        if m.get_type() == 'FTSV':
            ftsver = m['Hash']

        if apmver is not None and px4ver is not None and nuttxver is not None and ftsver is not None:
            break

    return (('ardupilot',apmver), ('PX4',px4ver), ('NuttX',nuttxver), ('FTS',ftsver))

def split_field_identifier(field_identifier):
    mobj = re.match(r'^(.+)\.(.+)$', field_identifier)
    return (mobj.group(1), mobj.group(2))

def combine_field_identifier(msg_name, field_name):
    return msg_name+'.'+field_name

def get_time_series(fn, field_identifiers):
    f = open(fn,'rb')
    parser = DFParser(f.read())
    f.close()

    split_field_names = [split_field_identifier(x) for x in field_identifiers]
    msg_names = set([x[0] for x in split_field_names])

    field_names = {}
    for msg_name in msg_names:
        field_names[msg_name] = []
        for field_identifier in filter(lambda x: split_field_identifier(x)[0] == msg_name, field_identifiers):
            field_names[msg_name].append(split_field_identifier(field_identifier)[1])

    t = dict([(msg_name,[]) for msg_name in msg_names])

    ret = {}
    for field_identifier in field_identifiers:
        msg_name, field_name = split_field_identifier(field_identifier)
        ret[field_identifier] = (t[msg_name],[])

    while True:
        m = parser.parse_next()
        if m is None:
            break

        msg_name = m.get_type()

        if msg_name in msg_names:
            t[msg_name].append(m['TimeUS']*1e-6)
            for field_name in field_names[msg_name]:
                field_identifier = combine_field_identifier(msg_name,field_name)
                ret[field_identifier][1].append(m[field_name])

    return ret

def generate_plot(plot_obj):
    if 'plots' not in plot_obj:
        return None

    fields = []
    for p in plot_obj['plots']:
        for f in p['fields']:
            fields.append(f)

    fields = set(fields)

    data = get_time_series(sys.argv[1], fields)

    plt.clf()
    plt.figure(figsize=(21,9), dpi=160)

    for p in plot_obj['plots']:
        if 'subplot' in p:
            plt.subplot(p['subplot'])

        plt.xlabel('Seconds')

        if 'y_unit' in p:
            plt.ylabel(p['y_unit'])

        for f in p['fields']:
            plt.plot(data[f][0],data[f][1],label=f)

        if 'y_range' in p:
            x1,x2,y1,y2 = plt.axis()
            plt.axis([None,None,p['y_range'][0],p['y_range'][1]])

        plt.legend()

    plot_img_data = StringIO()
    plt.savefig(plot_img_data)
    img = plot_img_data.getvalue().encode('base64')
    return '<h2>%s</h2><img width="100%%" src="data:image/png;base64,%s" />\n' % (plot_obj['name'], img)

workers = Pool(4)

plots = [
    {
        'name':'Flight mode',
        'plots': [
            {'fields': ['MODE.Mode']},
        ],
    },
    {
        'name':'FTS State',
        'plots': [
            {'fields': ['FTSS.State', 'FTSS.Rsn']},
        ],
    },
    {
        'name':'Throttle input and output',
        'plots': [
            {'fields': ['CTUN.ThI', 'CTUN.ThO']},
        ],
    },
    {
        'name':'Altitude',
        'plots': [
            {'y_unit': 'm', 'fields': ['CTUN.Alt', 'BARO.Alt']},
        ],
    },
    {
        'name':'Attitude control',
        'plots': [
            {'subplot':311, 'y_unit': 'Degrees', 'fields': ['ATT.Roll', 'ATT.DesRoll']},
            {'subplot':312, 'y_unit': 'Degrees', 'fields': ['ATT.Pitch', 'ATT.DesPitch']},
            {'subplot':313, 'y_unit': 'Degrees', 'fields': ['ATT.Yaw', 'ATT.DesYaw']},

        ],
    },
    {
        'name':'Motor outputs',
        'plots': [
            {'subplot':221, 'y_unit': 'PWM', 'fields': ['RCOU.C3']},
            {'subplot':222, 'y_unit': 'PWM', 'fields': ['RCOU.C1']},
            {'subplot':223, 'y_unit': 'PWM', 'fields': ['RCOU.C2']},
            {'subplot':224, 'y_unit': 'PWM', 'fields': ['RCOU.C4']},
        ],
    },
    {
        'name':'Temperatures',
        'plots': [
            {'y_unit':'C', 'fields': ['FTSS.BTINT', 'FTSS.BTTS1', 'IMU.Temp', 'IMU2.Temp', 'IMU3.Temp', 'BARO.Temp', 'BAR2.Temp', 'BAR3.Temp']},
        ],
    },
    {
        'name':'Power',
        'plots': [
            {'subplot':311, 'y_unit':'mV', 'fields': ['CURR.Volt']},
            {'subplot':312, 'y_unit':'mV', 'fields': ['FTSS.BC1mV', 'FTSS.BC2mV', 'FTSS.BC3mV']},
            {'subplot':313, 'y_unit':'pct', 'fields': ['FTSS.BSoC']},
        ],
    },
    {
        'name':'EKF Status',
        'plots': [
            {'subplot':411, 'fields': ['NKF4.PI']},
            {'subplot':412, 'fields': ['NKF4.SS', 'NKF9.SS']},
            {'subplot':413, 'fields': ['NKF4.GPS', 'NKF9.GPS']},
            {'subplot':414, 'fields': ['NKF4.TS', 'NKF9.TS']},
        ],
    },
    {
        'name':'EKF2 IMU1 Health Metrics',
        'plots': [
            {'subplot':211, 'y_range': (0,0.1), 'fields': ['NKF4.errRP']},
            {'subplot':212, 'fields': ['NKF4.SV', 'NKF4.SP', 'NKF4.SH', 'NKF4.SM']}
        ],
    },
    {
        'name':'EKF2 IMU2 Health Metrics',
        'plots': [
            {'subplot':211, 'y_range': (0,0.1), 'fields': ['NKF9.errRP']},
            {'subplot':212, 'fields': ['NKF9.SV', 'NKF9.SP', 'NKF9.SH', 'NKF9.SM']}
        ],
    },
    {
        'name':'Attitude',
        'plots': [
            {'subplot':311, 'y_unit': 'Degrees', 'fields': ['NKF1.Roll', 'NKF6.Roll', 'AHR2.Roll']},
            {'subplot':312, 'y_unit': 'Degrees', 'fields': ['NKF1.Pitch', 'NKF6.Pitch', 'AHR2.Pitch']},
            {'subplot':313, 'y_unit': 'Degrees', 'fields': ['NKF1.Yaw', 'NKF6.Yaw', 'AHR2.Yaw']},
        ],
    },
    {
        'name':'IMU Vibration',
        'plots': [
            {'subplot':311, 'y_unit': 'm/s/s', 'fields': ['VIBE.VibeX']},
            {'subplot':312, 'y_unit': 'm/s/s', 'fields': ['VIBE.VibeY']},
            {'subplot':313, 'y_unit': 'm/s/s', 'fields': ['VIBE.VibeZ']},
        ],
    },
    {
        'name':'IMU Clipping',
        'plots': [
            {'fields': ['VIBE.Clip0', 'VIBE.Clip1', 'VIBE.Clip2']},
        ],
    },
    {
        'name':'Accelerometers',
        'plots': [
            {'subplot':311, 'y_unit': 'm/s/s', 'fields': ['IMU.AccX', 'IMU2.AccX', 'IMU3.AccX']},
            {'subplot':312, 'y_unit': 'm/s/s', 'fields': ['IMU.AccY', 'IMU2.AccY', 'IMU3.AccY']},
            {'subplot':313, 'y_unit': 'm/s/s', 'fields': ['IMU.AccZ', 'IMU2.AccZ', 'IMU3.AccZ']},
        ],
    },
    {
        'name':'Gyros',
        'plots': [
            {'subplot':311, 'y_unit': 'm/s/s', 'fields': ['IMU.GyrX', 'IMU2.GyrX', 'IMU3.GyrX']},
            {'subplot':312, 'y_unit': 'm/s/s', 'fields': ['IMU.GyrY', 'IMU2.GyrY', 'IMU3.GyrY']},
            {'subplot':313, 'y_unit': 'm/s/s', 'fields': ['IMU.GyrZ', 'IMU2.GyrZ', 'IMU3.GyrZ']},
        ],
    },
    {
        'name':'Magnetometers',
        'plots': [
            {'subplot':311, 'y_unit': 'mGa', 'fields': ['MAG.MagX', 'MAG2.MagX', 'MAG3.MagX']},
            {'subplot':312, 'y_unit': 'mGa', 'fields': ['MAG.MagY', 'MAG2.MagY', 'MAG3.MagY']},
            {'subplot':313, 'y_unit': 'mGa', 'fields': ['MAG.MagZ', 'MAG2.MagZ', 'MAG3.MagZ']},
        ],
    },
    {
        'name':'Rangefinder',
        'plots': [
            {'y_unit': 'm', 'fields': ['RFND.Dist1', 'CTUN.SAlt']},
        ],
    },
    {
        'name':'GPS Satellites',
        'plots': [
            {'subplot':211, 'fields': ['GPS.NSats']},
            {'subplot':212, 'fields': ['GPS.HDop', 'GPA.VDop']},
        ],
    },
    {
        'name':'GPS Accuracy',
        'plots': [
            {'subplot':311, 'y_unit': 'm', 'fields': ['GPA.HAcc', 'GPA.VAcc']},
            {'subplot':312, 'y_unit': 'm/s', 'fields': ['GPA.SAcc']},
            {'subplot':313, 'fields': ['UBX1.jamInd']},
        ],
    },
    {
        'name':'Scheduler performance',
        'plots': [
            {'subplot':211, 'y_unit': 'us', 'y_range': (0,20000), 'fields': ['PM.MaxT']},
            {'subplot':212, 'fields': ['PM.LogDrop']},
        ],
    },
]


plot_images = workers.map(generate_plot, plots)

with open('out.html', 'w') as f:
    f.write('<html><body>')
    f.write('<h2>Component versions</h2>')
    f.write('<table border=1><tr><th>Component</th><th>Version</th></tr>')
    for v in get_versions(sys.argv[1]):
        f.write('<tr><td>%s</td><td>%s</td></tr>' % v)
    f.write('</table>')

    for img in plot_images:
        f.write(img+'<br />')
    f.write('</body></html>')
