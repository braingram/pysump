#!/usr/bin/env python
"""
Sump device settings:
    divider
    read/delay count
    flags

Trigger settings:
    masks
    values
    configurations
        delay
        level
        channel
        serial
        start
"""

import logging
import struct


logger = logging.getLogger(__name__)


default_settings = {
    'divider': 2,
    'read_count': 6140,
    'delay_count': 2048,
    'demux': False,
    'filter': False,
    'channel_groups': 0x0,
    'max_channel_groups': 4,
    'external': False,
    'inverted': False,
}

no_trigger = {
    'mask': 0,
    'value': 0,
    'delay': 0,
    'channel': 0,
    'level': 0,
    'start': True,
    'serial': False,
}

default_trigger = no_trigger.copy()
default_simple_trigger = no_trigger.copy()

trigger_op_codes = {
    'mask': ('\xc0', '\xc4', '\xc8', '\xcc'),
    'value': ('\xc1', '\xc5', '\xc9', '\xcd'),
    'config': ('\xc2', '\xc6', '\xca', '\xce'),
}

settings_op_codes = {
    'divider': '\x80',
    'count': '\x81',
    'flags': '\x82',
}


class Triggers(object):
    def __init__(self, triggers, n_stages=4):
        if hasattr(triggers, '__len__'):
            self.n_stages = len(triggers)
        else:
            self.n_stages = n_stages
        self.trigger_type = None
        if triggers is None:
            self.disable()
        if isinstance(triggers, (list, tuple)):
            self.complex(triggers)
        else:
            self.simple(triggers)

    def disable(self):
        logger.debug("Triggers.disable")
        self.trigger_type = 'None'
        self.stages = []
        for i in xrange(self.n_stages):
            t = no_trigger.copy()
            t['stage'] = i
            self.stages.append(t)

    def simple(self, trigger=None, **kwargs):
        logger.debug("Triggers.simple(%s)" % (trigger, ))
        if trigger is None:
            trigger = kwargs
        self.trigger_type = 'Simple'
        t = default_simple_trigger.copy()
        t.update(trigger)
        t['stage'] = 0
        self.stages = []
        self.stages.append(t)
        for i in xrange(1, self.n_stages):
            nt = no_trigger.copy()
            nt['stage'] = i
            nt['level'] = i
            self.stages.append(nt)

    def complex(self, stages):
        logger.debug("Triggers.complex(%s)" % (stages, ))
        self.trigger_type = 'Complex'
        for i in xrange(self.n_stages):
            if i >= len(stages):
                t = no_trigger.copy()
                t['stage'] = i
                t['level'] = i
                t['start'] = False
            else:
                t = default_trigger.copy()
                t['stage'] = i
                t['level'] = i
                t.update(stages[i])
            self.stages.append(t)

    def _pack_stage(self, stage_index):
        stage = self.stages[stage_index]
        msg = struct.pack(
            '<cHBB', trigger_op_codes['config'][stage_index],
            int(stage['delay']),
            ((int(stage['channel']) & 0x0F) << 4) | int(stage['level']),
            (int(stage['start']) << 3) | (int(stage['serial']) << 2) |
            ((int(stage['channel']) & 0x10) >> 4),
            )
        msg += struct.pack(
            '<ci', trigger_op_codes['mask'][stage_index], int(stage['mask']))
        msg += struct.pack(
            '<ci', trigger_op_codes['value'][stage_index], int(stage['value']))
        return msg

    def pack(self):
        return ''.join([self._pack_stage(i) for i in xrange(self.n_stages)])


class Settings(object):
    def __init__(self, settings=None, triggers=None):
        if settings is None:
            settings = {}
        s = default_settings.copy()
        s.update(settings)
        self.divider = s['divider']
        self.read_count = s['read_count']
        self.delay_count = s['delay_count']
        self.demux = s['demux']
        self.filter = s['filter']
        self.channel_groups = s['channel_groups']
        self.external = s['external']
        self.inverted = s['inverted']
        self.max_channel_groups = s['max_channel_groups']
        if not isinstance(triggers, Triggers):
            self.triggers = Triggers(triggers)

    def _pack_divider(self):
        d = self.divider - 1
        return struct.pack(
            '<cHBx', settings_op_codes['divider'],
            d & 0xFFFF, (d >> 16) & 0xFFFF)

    def _pack_count(self):
        """
        if delay_count == 0, trigger value should be in sample [0-3]
        if delay_count == read_count, it's possible
            the trigger value would NOT be present (1 beyond samples)
        """
        rc = self.read_count // 4
        self.read_count = rc * 4
        dc = self.delay_count // 4
        self.delay_count = dc * 4
        rc -= 1  # might be OLS specific
        return struct.pack('<cHH', settings_op_codes['count'], rc, dc)

    def _pack_flags(self):
        return struct.pack(
            '<cBxxx', settings_op_codes['flags'],
            (int(self.inverted) << 7) | (int(self.external) << 6) |
            (int(self.channel_groups) << 2) | (int(self.filter) << 1) |
            int(self.demux))

    def pack(self):
        return ''.join((
            self._pack_divider(), self.triggers.pack(),
            self._pack_count(), self._pack_flags()))
