#!/usr/bin/env python
from DFParser import DFParser
import sys
from math import *
import re
import matplotlib
matplotlib.use('Agg')
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
    parser = DFParser(f)

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

    f.close()

    return (('ardupilot',apmver), ('PX4',px4ver), ('NuttX',nuttxver), ('FTS',ftsver))

def split_field_identifier(field_identifier):
    mobj = re.match(r'^(.+)\.(.+)$', field_identifier)
    return (mobj.group(1), mobj.group(2))

def combine_field_identifier(msg_name, field_name):
    return msg_name+'.'+field_name

def get_time_series(fn, field_identifiers):
    f = open(fn,'rb')
    parser = DFParser(f)

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

    f.close()

    return ret

def generate_plot(args):
    bin_file, plot_obj = args
    if 'plots' not in plot_obj:
        return None

    fields = []
    for p in plot_obj['plots']:
        for f in p['fields']:
            fields.append(f)

    fields = set(fields)

    data = get_time_series(bin_file, fields)

    plt.figure(figsize=(21,9), dpi=160)

    for p in plot_obj['plots']:
        if 'subplot' in p:
            plt.subplot(p['subplot'])

        plt.xlabel('Seconds')

        if 'y_unit' in p:
            plt.ylabel(p['y_unit'])

        for f in p['fields']:
            plt.plot(data[f][0],data[f][1],label=f)

        x1,x2,y1,y2 = plt.axis()
        if 'y_range' in p:
            y1 = p['y_range'][0]
            y2 = p['y_range'][1]

        margin = (y2-y1)*0.05
        y1 = y1-margin
        y2 = y2+margin
        margin = (x2-x1)*0.05
        x1 = x1-margin
        x2 = x2+margin
        plt.axis([x1,x2,y1,y2])
        plt.legend()

    plot_img_data = StringIO()
    plt.savefig(plot_img_data)
    plt.close()
    img = plot_img_data.getvalue()
    return (plot_obj['name'], img)

def open_report(html):
    import SimpleHTTPServer
    import SocketServer
    import webbrowser
    import os
    import threading

    class CustomHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path=='/plots':
                self.send_response(200)
                self.send_header('Content-type','text/html')
                self.end_headers()
                self.wfile.write(html)
                return
            else:
                self.send_response(404)
                return

    httpd = SocketServer.TCPServer(("", 0), CustomHandler)
    threading.Thread(target=httpd.handle_request).start()
    webbrowser.open_new('http://'+httpd.server_address[0]+':'+str(httpd.server_address[1])+'/plots')

def generate_report(bin_file, plotsfile):
    workers = Pool(4)
    with open(plotsfile,'r') as f:
        plots = json.load(f)['plots']

    plot_images = workers.map(generate_plot, [(bin_file, x) for x in plots])

    html = ''
    html += '<html><body>'
    html += '<h1>%s</h1>' % bin_file
    html += '<h2>Component versions</h2>'
    html += '<table border=1><tr><th>Component</th><th>Version</th></tr>'
    for v in get_versions(bin_file):
        html += '<tr><td>%s</td><td>%s</td></tr>' % v
    html += '</table>'
    for name,img in plot_images:
        html += '<h2>%s</h2><img width="100%%" src="data:image/png;base64,%s" /><br />' % (name, img.encode('base64'))
    html += '</body></html>'

    return html

if __name__ == '__main__':
    with open(sys.argv[3], 'wb') as f:
        f.write(generate_report(sys.argv[2], sys.argv[1]))