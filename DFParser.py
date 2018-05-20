'''
Dataflash log file parser.
Derivative work of pymavlink/DFReader.py
'''

import struct
import os

def null_term(str):
    '''null terminate a string'''
    idx = str.find("\0")
    if idx != -1:
        str = str[:idx]
    return str

class DFFormat(object):
    def __init__(self, type, name, flen, format, columns):
        self.FORMAT_TO_STRUCT = {
            "b": ("b", None, int),
            "B": ("B", None, int),
            "h": ("h", None, int),
            "H": ("H", None, int),
            "i": ("i", None, int),
            "I": ("I", None, int),
            "f": ("f", None, float),
            "n": ("4s", None, str),
            "N": ("16s", None, str),
            "Z": ("64s", None, str),
            "c": ("h", 0.01, float),
            "C": ("H", 0.01, float),
            "e": ("i", 0.01, float),
            "E": ("I", 0.01, float),
            "L": ("i", 1.0e-7, float),
            "d": ("d", None, float),
            "M": ("b", None, int),
            "q": ("q", None, long),
            "Q": ("Q", None, long),
        }
        self.type = type
        self.name = name
        self.len = flen
        self.format = format
        self.columns = columns.split(',')

        if self.columns == ['']:
            self.columns = []

        msg_struct = "<"
        msg_mults = []
        msg_types = []
        for c in format:
            if ord(c) == 0:
                break
            try:
                (s, mul, type) = self.FORMAT_TO_STRUCT[c]
                msg_struct += s
                msg_mults.append(mul)
                msg_types.append(type)
            except KeyError as e:
                raise Exception("Unsupported format char: '%s' in message %s" % (c, name))

        self.msg_struct = msg_struct
        self.msg_types = msg_types
        self.msg_mults = msg_mults
        self.colhash = {}
        for i in range(len(self.columns)):
            self.colhash[self.columns[i]] = i

    def __str__(self):
        return "DFFormat(%s,%s,%s,%s)" % (self.type, self.name, self.format, self.columns)

class DFMessage(object):
    def __init__(self, fmt, elements):
        self.fmt = fmt
        self._elements = elements
        self._fieldnames = fmt.columns

    def __getitem__(self, field):
        '''override field getter'''
        try:
            i = self.fmt.colhash[field]
        except Exception:
            raise AttributeError(field)

        v = self.fmt.msg_types[i](self._elements[i])
        if self.fmt.msg_types[i] == str:
            v = null_term(v)
        if self.fmt.msg_mults[i] is not None:
            v *= self.fmt.msg_mults[i]
        return v

    def get_type(self):
        return self.fmt.name

    def __str__(self):
        ret = "%s {" % self.fmt.name
        col_count = 0
        for c in self.fmt.columns:
            ret += "%s : %s, " % (c, self.__getitem__(c))
            col_count += 1
        if col_count != 0:
            ret = ret[:-2]
        return ret + '}'

    def get_msgbuf(self):
        '''create a binary message buffer for a message'''
        values = []
        for i in range(len(self.fmt.columns)):
            if i >= len(self.fmt.msg_mults):
                continue
            mul = self.fmt.msg_mults[i]
            name = self.fmt.columns[i]
            if name == 'Mode' and 'ModeNum' in self.fmt.columns:
                name = 'ModeNum'
            v = self.__getitem__(name)
            if mul is not None:
                v /= mul
            values.append(v)
        return struct.pack("BBB", 0xA3, 0x95, self.fmt.type) + struct.pack(self.fmt.msg_struct, *values)

class DFParser:
    def __init__(self,f):
        self.HEAD1 = 0xA3
        self.HEAD2 = 0x95

        self.f = f
        f.seek(0, os.SEEK_END)
        self.data_len = f.tell()
        f.seek(0, os.SEEK_SET)

        self.formats = {
            0x80: DFFormat(0x80, 'FMT', 89, 'BBnNZ', "Type,Length,Name,Format,Columns")
        }
        self.msg_count = {
            0x80: 0
        }
        self.offset = 0

    def parse_next(self):
        f = self.f

        f.seek(self.offset, os.SEEK_SET)
        header = f.read(3)

        if len(header) < 3:
            return None

        while ord(header[0]) != self.HEAD1 or ord(header[1]) != self.HEAD2 or ord(header[2]) not in self.formats.keys():
            self.offset += 1
            if self.data_len - self.offset < 3:
                #end of log
                return None

        msg_type = ord(header[2])

        fmt = self.formats[msg_type]

        if self.data_len-self.offset < fmt.len:
            #end of log
            return None

        f.seek(self.offset+3, os.SEEK_SET)
        body = f.read(fmt.len-3)

        try:
            elements = list(struct.unpack(fmt.msg_struct,body))
        except Exception:
            # bad data, advance offset one byte and try again
            self.offset += 1
            return self.parse_next()


        self.msg_count[msg_type] += 1

        name = null_term(fmt.name)

        if name == 'FMT':
            try:
                self.formats[elements[0]] = DFFormat(elements[0],
                                                    null_term(elements[2]), elements[1],
                                                    null_term(elements[3]), null_term(elements[4]))
                self.msg_count[elements[0]] = 0
            except:
                pass

        self.offset += fmt.len

        try:
            m = DFMessage(fmt, elements)
        except ValueError:
            return self.parse_next()

        return m
