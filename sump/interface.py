#!/usr/bin/env python

# import sys

import logging
import struct

import serial

from . import errors
from . import fio
from . import ops
# import settings this as settings_module to avoid name conflicts
from . import settings as settings_module

logger = logging.getLogger(__name__)


class Interface(object):
    # undivided clock rate, in Hz, from testing with OBLS
    protocol_version = '1.0'

    def __init__(
            self, path='/dev/ttyACM0', baud=115200,
            timeout=None, settings=None):
        self.timeout = timeout
        if settings is None:
            self.settings = settings_module.Settings()
        self.port = serial.Serial(path, baud, timeout=self.timeout)
        self.debug_logger = None
        self.reset()
        self.metadata = self.query_metadata()
        self.settings = None

    def reset(self):
        logger.debug("reset")
        self.port.write('\x00\x00\x00\x00\x00')

    def capture(self, send_settings=True):
        '''Request a capture.'''
        logger.debug("capture")
        if send_settings:
            self.send_settings()
        # get local references to objects for faster execution ..
        ufs = []
        for i in xrange(4):
            if not (self.settings.channel_groups & (0b1 < i)):
                ufs.append(lambda c, si=i: ord(c) << (8 * si))

        d = []
        self.port.timeout = self.settings.timeout
        self.port.write('\x01')  # start the capture
        for _ in xrange(self.settings.read_count):
            v = 0
            for uf in ufs:
                v |= uf(self.port.read(1))
            d.append(v)

        self.reset()  # TODO is this needed?
        if self.settings.latest_first:
            return d[::-1]
        else:
            return d

    def save(self, capture, filename, meta=None):
        logger.debug("save %s", filename)
        fio.save(capture, filename, self.settings, meta)

    def id_string(self):
        '''Return device's SUMP ID string.'''
        logger.debug("id_string")
        self.port.write('\x02')
        # TODO check protocol version here
        val = self.port.read(4)  # 4 bytes as a small-endian int
        return val[::-1]

    def xon(self):
        logger.debug("xon")
        self.port.write('\x11')

    def xoff(self):
        logger.debug("xoff")
        self.port.write('\x13')

    def _send_trigger_mask(self, stage, mask):
        logger.debug("send_trigger_mask %s %s", stage, mask)
        #w = self.port.write
        #w = self._trace_control('Trigger mask')
        msg = struct.pack('<Bi', 0xC0 | (stage << 2), mask)
        self.port.write(msg)
        #w(chr(0xC0 | (stage << 2)))
        #w(chr(mask & 0xFF))
        #w(chr((mask >> 8) & 0xFF))
        #w(chr((mask >> 16) & 0xFF))
        #w(chr((mask >> 24) & 0xFF))

    def _send_trigger_value(self, stage, value):
        logger.debug("send_trigger_value %s %s", stage, value)
        #w = self.port.write
        #w = self._trace_control('Trigger values')
        msg = struct.pack('<Bi', 0xC1 | (stage << 2), value)
        self.port.write(msg)
        #w(chr(0xC1 | (stage << 2)))
        #w(chr(values & 0xFF))
        #w(chr((values >> 8) & 0xFF))
        #w(chr((values >> 16) & 0xFF))
        #w(chr((values >> 24) & 0xFF))

    def _send_trigger_configuration(
            self, stage, delay, channel, level, start, serial):
        logger.debug(
            "send_trigger_configuration %s %s %s %s %s %s",
            stage, delay, channel, level, start, serial)
        msg = struct.pack(
            '<BHBB',
            0xC2 | (stage << 2),
            delay,
            ((channel & 0x0F) << 4) | level,
            (start << 3) | (serial << 2) | ((channel & 0x10) >> 4))
        self.port.write(msg)
        #w = self.port.write
        #w = self._trace_control('Trigger config')
        #w(chr(0xC2 | (stage << 2)))
        #d = delay
        #w(chr(d & 0xFF))
        #w(chr((d >> 8) & 0xFF))
        #c = channel
        #w(chr(((c & 0x0F) << 4) | level))
        #w(chr((start << 3) | (serial << 2) | ((c & 0x10) >> 4)))

    def send_divider_settings(self, settings):
        logger.debug("send_divider_settings %s", settings.divider)
        d = settings.divider - 1  # offset 1 correction for SUMP hardware
        msg = struct.pack('<cHBx', '\x80', d & 0xFFFF, d >> 16)
        self.port.write(msg)
        #w = self.port.write
        ##w = self._trace_control('Divider')
        #w('\x80')
        #d = settings.divider - 1  # offset 1 correction for SUMP hardware
        #w(chr(d & 0xFF))
        #w(chr((d >> 8) & 0xFF))
        #w(chr((d >> 16) & 0xFF))
        #w('\x00')

    def send_read_and_delay_count_settings(self, settings):
        logger.debug("send_read_and_delay_count_settings")
        r = (settings.read_count + 3) >> 2
        d = (settings.delay_count + 3) >> 2
        msg = struct.pack('<cHH', '\x81', r, d)
        self.port.write(msg)
        #w = self.port.write
        ##w = self._trace_control('Read/Delay')
        #w('\x81')
        ## factor 4 correction for SUMP hardware
        #r = (settings.read_count + 3) >> 2
        #w(chr(r & 0xFF))
        #w(chr((r >> 8) & 0xFF))
        ## factor 4 correction for SUMP hardware
        #d = (settings.delay_count + 3) >> 2
        #w(chr(d & 0xFF))
        #w(chr((d >> 8) & 0xFF))

    def send_flags_settings(self, settings):
        logger.debug("send_flag_settings")
        msg = struct.pack(
            '<cBxxx', '\x82',
            (settings.inverted << 7) | (settings.external << 6) |
            (settings.channel_groups << 2) | (settings.filter << 1) |
            settings.demux)
        self.port.write(msg)
        #w = self.port.write
        ##w = self._trace_control('Flags')
        #w('\x82')
        #w(chr((settings.inverted << 7)
        #      | (settings.external << 6)
        #      | (settings.channel_groups << 2)
        #      | (settings.filter << 1)
        #      | settings.demux
        #      ))
        ## disable RLE compression, alternate number scheme, test modes
        #w('\x00')
        #w('\x00')
        #w('\x00')

    def send_settings(self):
        """
        The order of things in this function are CRITICAL
        """
        logger.debug("send_settings")
        self.send_divider_settings(self.settings)
        trigger_enable = self.settings.trigger_enable
        if trigger_enable == 'None':
            # send always-trigger trigger settings
            for stage in xrange(self.settings.trigger_max_stages):
                self._send_trigger_configuration(stage, 0, 0, 0, True, False)
                self._send_trigger_mask(stage, 0)
                self._send_trigger_values(stage, 0)
        elif trigger_enable == 'Simple':
            # set settings from stage 0, no-op for stages 1..3
            self._send_trigger_configuration(
                0, self.settings.trigger_stages[0].delay,
                self.settings.trigger_stages[0].channel,
                0, True, self.settings.trigger_stages[0].serial)
            self._send_trigger_mask(0, self.settings.trigger_stages[0].mask)
            self._send_trigger_values(0, self.settings.trigger_stages[0].value)
            for stage in xrange(1, self.self.settings.trigger_max_stages):
                self._send_trigger_configuration(stage, 0, 0, 0, False, False)
                self._send_trigger_mask(stage, 0)
                self._send_trigger_values(stage, 0)
        elif trigger_enable == 'Complex':
            for (i, stage) in enumerate(self.settings.trigger_stages):
                # OLS needs things in this order
                self._send_trigger_mask(i, stage.mask)
                self._send_trigger_values(i, stage.value)
                self._send_trigger_configuration(
                    i, stage.delay, stage.channel, stage.level, stage.start,
                    stage.serial)
        else:
            raise errors.TriggerEnableError
        self.send_read_and_delay_count_settings(self.settings)
        self.send_flags_settings(self.settings)

    def query_metadata(self):
        '''Return metadata identifying the SUMP device,
        firmware, version, etc.'''
        logger.debug("query_metadata")
        result = []
        self.reset()
        r = self.port.read
        timeout = self.port.timeout  # save timeout setting to restore later
        try:
            # only wait 2 seconds for devices that don't do metadata
            self.port.timeout = 2
            self.port.write('\x04')
            while True:
                token = r(1)
                if not token:		# end-of-file
                    break
                token = ord(token)
                if not token:		# binary 0 end-of-metadata marker
                    break

                elif token <= 0x1F:  # C-string follows token
                    v = []
                    while True:
                        x = r(1)
                        if x != '\0':
                            v .append(x)
                        else:
                            break
                    result.append((token, ''.join(v)))

                elif token <= 0x3F:  # 32-bit int follows token
                    result.append((token, ops.big_endian(r(4))))

                elif token <= 0x5F:  # 8-bit int follows token
                    result.append((token, ord(r(1))))

                else:
                    result.append((token, None))
        finally:
            self.port.timeout = timeout  # restore timeout setting
        return result

    def close(self):
        logger.debug("close")
        self.port.close()
        self.port = None


def open_interface(port=None, baud=None, **kwargs):
    s = settings_module.Settings()
    for kw in kwargs:
        setattr(s, kw, kwargs[kw])
    i = Interface(port, baud)
    i.settings = s
    i.send_settings(s)
    return i
