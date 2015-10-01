#!/usr/bin/env python

import serial

from ..settings import Settings

defaults = {
    'port': '/dev/ttyACM0',
    'baud': 115200,
    'timeout': None,
}


class RS232Sump(object):
    def __init__(self, port=None, baud=None, timeout=None, settings=None):
        if settings is None:
            settings = {}
        self.settings = Settings(settings)
        if port is None:
            port = settings.get('path', defaults['port'])
        self.port_string = port
        if baud is None:
            baud = settings.get('baud', defaults['baud'])
        self.baud = baud
        if timeout is None:
            timeout = settings.get('timeout', defaults['timeout'])
        self.timeout = timeout
        self.port = None
        self.connect()

    def connect(self):
        if self.port is not None:
            self.disconnect()
        self.port = serial.Serial(
            self.port_string, self.baud, timeout=self.timeout)

    def disconnect(self):
        if self.port is None:
            return
        self.port.close()
        self.port = None

    def __del__(self):
        self.disconnect()

    def _send_settings(self):
        pass

    def reset(self, hard=True):
        if hard:
            self.port.write('\x00\x00\x00\x00\x00')
        else:
            self.port.write('\x00')

    def id_string(self):
        self.port.write('\x02')
        return self.port.read(4)[::-1]

    def xon(self):
        self.port.write('\x11')

    def xoff(self):
        self.port.write('\x13')

    def _build_unpack_functions(self):
        ufs = []
        for i in xrange(self.settings.max_channel_groups):
            if not self.settings.channel_groups & (0b1 << i):
                o = 8 * i
                ufs.append(lambda c, o=o: ord(c) << o)
        return ufs

    def capture(self):
        ufs = self._build_unpack_functions()
        d = [0] * self.settings.read_count
        self.port.write('\x01')
        for i in xrange(self.settings.read_count):
            v = 0
            for uf in ufs:
                v |= uf(self.port.read(1))
            d[i] = v
        return d
