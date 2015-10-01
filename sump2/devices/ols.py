#!/usr/bin/env python

import logging
import struct

from . import rs232


logger = logging.getLogger(__name__)


def read_string(port):
    s = []
    c = port.read(1)
    while c != '\x00':
        s.append(c)
        c = port.read(1)
    return ''.join(s)


def read_uint(port):
    return struct.unpack('>I', port.read(4))[0]


def read_ubyte(port):
    return struct.unpack('B', port.read(1))[0]


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
    def __init__(self, port=None, baud=None, timeout=None, settings=None):
        rs232.RS232Sump.__init__(self, port, baud, timeout, settings)
        self._max_sample_rate = None
        if settings is None:
            self._autoconfigure()

    def get_sample_rate(self):
        if self._max_sample_rate is None:
            md = self.metadata()
            if 'Max Sample Rate' not in md:
                raise Exception(
                    "unknown max sample rate, cannot set sample rate")
            self._max_sample_rate = md['Max Sample Rate']
        return self._max_sample_rate / float(self.settings.divider)

    def set_sample_rate(self, rate):
        if self._max_sample_rate is None:
            md = self.metadata()
            if 'Max Sample Rate' not in md:
                raise Exception(
                    "unknown max sample rate, cannot set sample rate")
            self._max_sample_rate = md['Max Sample Rate']
        self.settings.divider = int(self._max_sample_rate / float(rate))

    def _autoconfigure(self):
        md = self.metadata()
        nb = md.get('Sample Memory', 24576)
        self.settings.delay_count = 0
        nprobes = md.get('N Probes (short)', md.get('N Probes', None))
        if nprobes is not None:
            if nprobes == 8:
                self.settings.channel_groups = 0b1110
                self.settings.read_count = nb
            elif nprobes == 16:
                self.settings.channel_groups = 0b1100
                self.settings.read_count = nb // 2
            elif nprobes == 32:
                self.settings.channel_groups = 0b0
                self.settings.read_count = nb // 4

    def metadata(self):
        logger.debug("OLS.metadata")
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
