#!/usr/bin/env python

from . import defaults


class Settings (object):
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
        stages = defaults.MAX_TRIGGER_STAGES
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
        o = Settings()  # other instance
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
