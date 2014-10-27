#!/usr/bin/env python

# import sys

import serial

from . import defaults
from . import errors
from . import fio
from . import ops
# import settings this as settings_module to avoid name conflicts
from . import settings as settings_module


class Interface(object):
    # undivided clock rate, in Hz, from testing with OBLS
    clock_rate = 100000000
    protocol_version = '1.0'

    def __init__(self, path=None, baud=None, timeout=None):
        self.timeout = timeout
        if path is None:
            path = defaults.PATH
        if baud is None:
            baud = defaults.BAUD
        self.port = serial.Serial(path, baud, timeout=self.timeout)
        self.debug_logger = None
        self.reset()
        self.metadata = self.query_metadata()
        self.settings = None

    def reset(self):
        w = self.port.write
        w('\x00')
        w('\x00')
        w('\x00')
        w('\x00')
        w('\x00')

    def capture(self, settings=None):
        '''Request a capture.'''
        if settings is None:
            settings = self.settings
        if settings is None:
            raise errors.SettingsError("capture must have access to settings")
        # get local references to objects for faster execution ..
        ufs = []
        for i in xrange(4):
            if not (settings.channel_groups & (i + 1)):
                ufs.append(lambda c: ord(c) << (8 * i))

        d = []
        self.port.timeout = settings.timeout
        self.port.write('\x01')  # start the capture
        for _ in xrange(settings.read_count):
            v = 0
            for uf in ufs:
                v |= uf(self.port.read(1))
            d.append(v)

        self.reset()  # TODO is this needed?
        if settings.latest_first:
            return d[::-1]
        else:
            return d

    def save(self, capture, filename, meta=None):
        fio.save(capture, filename, self.settings, meta)

    def id_string(self):
        '''Return device's SUMP ID string.'''
        self.port.write('\x02')
        val = self.port.read(4)  # 4 bytes as a small-endian int
        return val[::-1]

    def xon(self):
        self.port.write('\x11')

    def xoff(self):
        self.port.write('\x13')

    def _trace_control(self, legend):
        if self.debug_logger is None:
            return self.port.write
        else:
            w = self.port.write
            logger = self.debug_logger
            logger.write('\n' + legend + ' \t')

            def tw(data):
                logger.write('%02x' % (ord(data),))
                logger.flush()
                w(data)
            return tw

    def _send_trigger_mask(self, stage, mask):
        # w = self.port.write
        w = self._trace_control('Trigger mask')
        w(chr(0xC0 | (stage << 2)))
        w(chr(mask & 0xFF))
        w(chr((mask >> 8) & 0xFF))
        w(chr((mask >> 16) & 0xFF))
        w(chr((mask >> 24) & 0xFF))

    def send_trigger_mask_settings(self, settings):
        # w = self.port.write
        w = self._trace_control('Trigger mask')
        for stage in xrange(defaults.MAX_TRIGGER_STAGES):
            m = settings.trigger_mask[stage]
            w(chr(0xC0 | (stage << 2)))
            w(chr(m & 0xFF))
            w(chr((m >> 8) & 0xFF))
            w(chr((m >> 16) & 0xFF))
            w(chr((m >> 24) & 0xFF))

    def _send_trigger_values(self, stage, values):
        # w = self.port.write
        w = self._trace_control('Trigger values')
        w(chr(0xC1 | (stage << 2)))
        w(chr(values & 0xFF))
        w(chr((values >> 8) & 0xFF))
        w(chr((values >> 16) & 0xFF))
        w(chr((values >> 24) & 0xFF))

    def send_trigger_values_settings(self, settings):
        # w = self.port.write
        w = self._trace_control('Trigger values')
        for stage in xrange(defaults.MAX_TRIGGER_STAGES):
            v = settings.trigger_values[stage]
            w(chr(0xC1 | (stage << 2)))
            w(chr(v & 0xFF))
            w(chr((v >> 8) & 0xFF))
            w(chr((v >> 16) & 0xFF))
            w(chr((v >> 24) & 0xFF))

    def _send_trigger_configuration(
            self, stage, delay, channel, level, start, serial):
        # w = self.port.write
        w = self._trace_control('Trigger config')
        w(chr(0xC2 | (stage << 2)))
        d = delay
        w(chr(d & 0xFF))
        w(chr((d >> 8) & 0xFF))
        c = channel
        w(chr(((c & 0x0F) << 4) | level))
        w(chr((start << 3) | (serial << 2) | ((c & 0x10) >> 4)))

    def send_trigger_configuration_settings(self, settings):
        # w = self.port.write
        w = self._trace_control('Trigger config')
        for stage in xrange(defaults.MAX_TRIGGER_STAGES):
            w(chr(0xC2 | (stage << 2)))
            d = settings.trigger_delay[stage]
            w(chr(d & 0xFF))
            w(chr((d >> 8) & 0xFF))
            c = settings.trigger_channel[stage]
            w(chr(((c & 0x0F) << 4) | settings.trigger_level[stage]))
            w(chr((settings.trigger_start[stage] << 3) | (
                settings.trigger_serial[stage] << 2) | ((c & 0x10) >> 4)))

    def send_divider_settings(self, settings):
        # w = self.port.write
        w = self._trace_control('Divider')
        w('\x80')
        d = settings.divider - 1  # offset 1 correction for SUMP hardware
        w(chr(d & 0xFF))
        w(chr((d >> 8) & 0xFF))
        w(chr((d >> 16) & 0xFF))
        w('\x00')

    def send_read_and_delay_count_settings(self, settings):
        # w = self.port.write
        w = self._trace_control('Read/Delay')
        w('\x81')
        # factor 4 correction for SUMP hardware
        r = (settings.read_count + 3) >> 2
        w(chr(r & 0xFF))
        w(chr((r >> 8) & 0xFF))
        # factor 4 correction for SUMP hardware
        d = (settings.delay_count + 3) >> 2
        w(chr(d & 0xFF))
        w(chr((d >> 8) & 0xFF))

    def send_flags_settings(self, settings):
        # w = self.port.write
        w = self._trace_control('Flags')
        w('\x82')
        w(chr((settings.inverted << 7)
              | (settings.external << 6)
              | (settings.channel_groups << 2)
              | (settings.filter << 1)
              | settings.demux
              ))
        # disable RLE compression, alternate number scheme, test modes
        w('\x00')
        w('\x00')
        w('\x00')

    def send_settings(self, settings):
        self.send_divider_settings(settings)
        self.send_read_and_delay_count_settings(settings)
        self.send_flags_settings(settings)
        trigger_enable = settings.trigger_enable
        if trigger_enable == 'None':
            # send always-trigger trigger settings
            for stage in xrange(defaults.MAX_TRIGGER_STAGES):
                self._send_trigger_configuration(stage, 0, 0, 0, True, False)
                self._send_trigger_mask(stage, 0)
                self._send_trigger_values(stage, 0)
        elif trigger_enable == 'Simple':
            # set settings from stage 0, no-op for stages 1..3
            self._send_trigger_configuration(
                0, settings.trigger_delay[0], settings.trigger_channel[0],
                0, True, settings.trigger_serial[0])
            self._send_trigger_mask(0, settings.trigger_mask[0])
            self._send_trigger_values(0, settings.trigger_values[0])
            for stage in xrange(1, defaults.MAX_TRIGGER_STAGES):
                self._send_trigger_configuration(stage, 0, 0, 0, False, False)
                self._send_trigger_mask(stage, 0)
                self._send_trigger_values(stage, 0)
        elif trigger_enable == 'Complex':
            self.send_trigger_configuration_settings(settings)
            self.send_trigger_mask_settings(settings)
            self.send_trigger_values_settings(settings)
        else:
            raise errors.TriggerEnableError

    def set_logfile(self, logfile):
        self.debug_logger = logfile

    def query_metadata(self):
        '''Return metadata identifying the SUMP device,
        firmware, version, etc.'''
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
