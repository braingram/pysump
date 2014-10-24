# -*- coding: ASCII -*-
'''Interface with SUMP logic-analyzer device.
Copyright 2011, Mel Wilson mwilson@melwilsonsoftware.ca

This file is part of pyLogicSniffer.

    pyLogicSniffer is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    pyLogicSniffer is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with pyLogicSniffer.  If not, see <http://www.gnu.org/licenses/>.
'''

import serial
import sys
import numpy

SUMP_BAUD = 115200
SUMP_PATH = '/dev/ttyACM0'
MAX_TRIGGER_STAGES = 4


class SumpError (StandardError):
    '''Errors raised by the SUMP client.'''


class SumpIdError (SumpError):
    '''The wrong string was returned by an ID request.'''


class SumpFlagsError (SumpError):
    '''Illegal combination of flags.'''


class SumpTriggerEnableError (SumpError):
    '''Illegal trigger enable setting.'''


class SumpStageError (SumpError):
    '''Illegal trigger stage setting.'''


def big_endian(s4):
    '''Re-cast 4 bytes as 32-bit int, MSB first.'''
    return (ord(s4[0]) << 24) | (ord(s4[1]) << 16) | \
        (ord(s4[2]) << 8) | ord(s4[3])


def little_endian(s4):
    '''Re-cast 4 bytes as 32-bit int, LSB first.'''
    return (ord(s4[3]) << 24) | (ord(s4[2]) << 16) | \
        (ord(s4[1]) << 8) | ord(s4[0])


class SumpDeviceSettings (object):
    '''Sampling and trigger parameters.'''
    # undivided clock rate, in Hz, from testing with OBLS
    clock_rate = 100000000

    def __init__(self):
        self.default()

    def default(self):
        '''Non-impossible default settings.'''
        # general settings ..
        self.timeout = None
        self.latest_first = True
        self.divider = 2			# default sampling rate 50MHz
        self.read_count = 4096		# default sampling size
        self.delay_count = 2048		# default before/after 50/50
        self.external = False			# True for external trigger
        self.inverted = False			# True to invert external trigger
        # true to filter out glitches shorter than 1/(200MHz)
        self.filter = False
        self.demux = False			# True for double-speed sampling
        self.channel_groups = 0x0  # default all channel groups

        self.trigger_enable = 'None'
        # trigger settings, by stage ..
        stages = MAX_TRIGGER_STAGES
        self.trigger_mask = [0] * stages			# 32-bit mask for trigger channels
        # 32-bit match-readings for trigger channels
        self.trigger_values = [0] * stages
        self.trigger_delay = [0] * stages			# post-trigger delay in samples
        # user-preferred units for trigger_delay display
        self.trigger_delay_unit = [0] * stages
        # level at which trigger stage is armed
        self.trigger_level = [0] * stages
        self.trigger_channel = [0] * stages		# channel for serial trigger
        # default parallel trigger testing
        self.trigger_serial = [False] * stages
        # default immediate start from stage 0
        self.trigger_start = [True] + [False] * (stages - 1)

    def clone(self):
        '''Clone an independent copy of these settings.'''
        o = SumpDeviceSettings()  # other instance
        self.copy(o)
        return o

    def copy(self, other):
        '''Copy these settings to another instance.'''
        other.divider = self.divider
        other.read_count = self.read_count
        other.delay_count = self.delay_count
        other.external = self.external
        other.inverted = self.inverted
        other.filter = self.filter
        other.demux = self.demux
        other.channel_groups = self.channel_groups

        other.trigger_enable = self.trigger_enable

        # trigger settings, by stage ..
        other.trigger_mask[:] = self.trigger_mask
        other.trigger_values[:] = self.trigger_values
        other.trigger_delay[:] = self.trigger_delay
        other.trigger_delay_unit[:] = self.trigger_delay_unit
        other.trigger_level[:] = self.trigger_level
        other.trigger_channel[:] = self.trigger_channel
        other.trigger_serial[:] = self.trigger_serial
        other.trigger_start[:] = self.trigger_start

    def get_sample_rate(self):
        '''Return the sample rate called for by these settings.'''
        rate = int(self.clock_rate / self.divider)
        if self.demux:
            rate *= 2
        return rate


class SumpInterface (object):
    # undivided clock rate, in Hz, from testing with OBLS
    clock_rate = 100000000
    protocol_version = '1.0'

    def __init__(self, path, baud=SUMP_BAUD, timeout=None):
        self.timeout = timeout
        self.port = serial.Serial(path, baud, timeout=self.timeout)
        self.debug_logger = None
        self.reset()
        self.metadata = self.query_metadata()

    def reset(self):
        w = self.port.write
        w('\x00')
        w('\x00')
        w('\x00')
        w('\x00')
        w('\x00')

    def capture(self, settings):
        '''Request a capture.'''
        # get local references to objects for faster execution ..
        read_count = settings.read_count
        mask = settings.channel_groups
        read = self.port.read
        ord_ = ord

        sys.stderr.write('reading %d\n' % (read_count,))
        sys.stderr.flush()
        d = numpy.zeros((read_count,), dtype=numpy.uint32)
        if settings.latest_first:
            # readings arrive most-recent-first
            data_sequence = xrange(read_count - 1, -1, -1)
        else:
            data_sequence = xrange(read_count)
        self.port.timeout = settings.timeout
        self.port.write('\x01')  # start the capture
        for i in data_sequence:
            v = 0
            if not (mask & 1):
                v |= ord_(read(1))
            if not (mask & 2):
                v |= ord_(read(1)) << 8
            if not (mask & 4):
                v |= ord_(read(1)) << 16
            if not (mask & 8):
                v |= ord_(read(1)) << 24
            d[i] = v
        self.reset()
        return d

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
        for stage in xrange(MAX_TRIGGER_STAGES):
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
        for stage in xrange(MAX_TRIGGER_STAGES):
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
        for stage in xrange(MAX_TRIGGER_STAGES):
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
            for stage in xrange(MAX_TRIGGER_STAGES):
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
            for stage in xrange(1, MAX_TRIGGER_STAGES):
                self._send_trigger_configuration(stage, 0, 0, 0, False, False)
                self._send_trigger_mask(stage, 0)
                self._send_trigger_values(stage, 0)
        elif trigger_enable == 'Complex':
            self.send_trigger_configuration_settings(settings)
            self.send_trigger_mask_settings(settings)
            self.send_trigger_values_settings(settings)
        else:
            raise SumpTriggerEnableError

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
                    result.append((token, big_endian(r(4))))

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
