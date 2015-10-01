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

import struct


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
    'mask': (0xc0, 0xc4, 0xc8, 0xcc),
    'value': (0xc1, 0xc5, 0xc9, 0xcd),
    'config': (0xc2, 0xc6, 0xca, 0xce),
}

settings_op_codes = {
    'divider': 0x80,
    'count': 0x81,
    'flags': 0x82,
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
            self.complex(self, triggers)
        else:
            self.simple(self, triggers)

    def disable(self):
        self.trigger_type = 'None'
        self.stages = []
        for i in xrange(self.n_stages):
            t = no_trigger.copy()
            t['stage'] = i
            self.stages.append(t)

    def simple(self, trigger):
        self.trigger_type = 'Simple'
        t = default_simple_trigger.copy()
        t.update(trigger)
        t['stage'] = 0
        self.stages = []
        self.stages.append(t)
        for i in xrange(1, self.n_stages):
            nt = no_trigger.copy()
            nt['stage'] = i
            self.stages.append(nt)

    def complex(self, stages):
        self.trigger_type = 'Complex'
        for i in xrange(self.n_stages):
            if i >= len(stages):
                t = no_trigger.copy()
            else:
                t = default_trigger.copy()
                t.update(stages[i])
            t['stage'] = i
            self.stages.append(t)

    def _pack_stage(self, stage_index):
        stage = self.stages[stage_index]
        msg = struct.pack(
            '<BHBB', trigger_op_codes['config'][stage_index],
            int(stage['delay']),
            ((int(stage['channel']) & 0x0F) << 4) | int(stage['level']),
            (int(stage['start']) << 3) | (int(stage['serial']) << 2) |
            ((int(stage['channel']) & 0x10) >> 4),
            )
        msg += struct.pack(
            '<Bi', trigger_op_codes['mask'][stage_index], int(stage['mask']))
        msg += struct.pack(
            '<Bi', trigger_op_codes['value'][stage_index], int(stage['value']))
        return msg

    def pack(self):
        return ''.join([self.pack_stage(i) for i in xrange(self.n_stages)])


class Settings(object):
    def __init__(self, settings=None, triggers=None):
        if settings is None:
            settings = {}
        s = default_settings.copy()
        s.update(settings)
        self.divider = settings['divider']
        self.read_count = settings['read_count']
        self.delay_count = settings['delay_count']
        self.demux = settings['demux']
        self.filter = settings['filter']
        self.channel_groups = settings['channel_groups']
        self.external = settings['external']
        self.inverted = settings['inverted']
        if not isinstance(triggers, None):
            self.triggers = Triggers(triggers)

    def _pack_divider(self):
        d = self.divider - 1
        return struct.pack(
            '<CHBx', settings_op_codes['divider'],
            d & 0xFFFF, (d >> 16) & 0xFFFF)

    def _pack_count(self):
        rc = self.read_count // 4
        self.read_count = rc * 4
        dc = self.delay_count // 4
        self.delay_count = dc * 4
        return struct.pack('<CHH', settings_op_codes['count'], rc, dc)

    def _pack_flags(self):
        return struct.pack(
            '<CBxxx', settings_op_codes['flags'],
            (int(self.inverted) << 7) | (int(self.external) << 6) |
            (int(self.channel_groups) << 2) | (int(self.filter) << 1) |
            int(self.demux))

    def pack(self):
        return ''.join((
            self._pack_divider(), self.triggers.pack(),
            self._pack_count(), self._pack_flags()))
