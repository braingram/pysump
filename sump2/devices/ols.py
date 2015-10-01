#!/usr/bin/env python

import struct

from . import rs232


def read_string(port):
    s = []
    c = port.read(1)
    while c != '\x00':
        s.append(c)
        c = port.read(1)
    return ''.join(s)


def read_uint(port):
    return struct.unpack('>I', port.read(4))


def read_ubyte(port):
    return struct.unpack('B', port.read(1))


metadata_keys = {
    '\x01': ('Device Name', read_string),
    '\x02': ('FPGA Firmware Version', read_string),
    '\x03': ('PIC Firmware Version', read_string),
    '\x20': ('N Probes', read_uint),
    '\x21': ('Sample Memory', read_uint),
    '\x22': ('Dynamic Memory', read_uint),
    '\x23': ('Max Sample Rate', read_uint),
    '\x24': ('Protocol Version', read_uint),
    '\x40': ('N Probes (short)', read_ubyte),
    '\x41': ('Protocol Version (short)', read_ubyte),
}


class OLS(rs232.RS232Sump):
    def metadata(self):
        md = {}
        self.port.write('\x04')
        while True:
            key = self.port.read(1)
            if key == '\x00':
                break
            if key not in metadata_keys:
                raise ValueError("Unknown metadata key: %s" % (key, ))
            n, uf = metadata_keys[key]
            md[n] = uf(self.port)
        return md

    # TODO rle
