#!/usr/bin/env python

import hashlib
import logging
import pickle

import numpy
import serial

from ..settings import Settings

defaults = {
    'port': '/dev/ttyACM0',
    'baud': 115200,
    'timeout': None,
}


capture_dtypes = [
    numpy.uint8, numpy.uint16, numpy.uint32, numpy.uint32,
    numpy.uint64, numpy.uint64]

logger = logging.getLogger(__name__)


class RS232Sump(object):
    def __init__(self, port=None, baud=None, timeout=None, settings=None):
        if settings is None:
            settings = {}
        self.settings = Settings(settings)
        self._settings_hash = None
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
        logger.debug(
            "RS232Sump.__init__(%s, %s, %s, %s)",
            port, baud, timeout, settings)
        self.connect()

    def connect(self):
        logger.debug("RS232Sump.connect")
        if self.port is not None:
            self.disconnect()
        self.port = serial.Serial(
            self.port_string, self.baud, timeout=self.timeout)

    def disconnect(self):
        logger.debug("RS232Sump.disconnect")
        if self.port is None:
            return
        self.port.close()
        self.port = None

    def __del__(self):
        logger.debug("RS232Sump.__del__")
        self.disconnect()

    def send_settings(self):
        logger.debug("RS232Sump.send_settings")
        self.reset()
        h = self.settings.pack()
        self.port.write(self.settings.pack())
        self._settings_hash = h

    def _check_settings_hash(self):
        """False if settings need updated"""
        if self._settings_hash is None:
            return False
        h = self.settings.pack()
        if h != self._settings_hash:
            return False
        return True

    def reset(self, hard=True):
        logger.debug("RS232Sump.reset")
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
        logger.debug("RS232Sump.capture")
        if not self._check_settings_hash():
            self.send_settings()
        ufs = self._build_unpack_functions()
        logger.debug(
            "RS232Sump.capture: built %i unpack functions" %
            len(ufs))
        # include trigger value
        n_samples = self.settings.read_count
        dt = capture_dtypes[len(ufs)]
        d = numpy.empty(n_samples, dtype=dt)
        self.port.write('\x01')
        for i in xrange(n_samples):
            v = 0
            for uf in ufs:
                v |= uf(self.port.read(1))
            d[i] = v
        return d
