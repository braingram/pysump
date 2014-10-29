#!/usr/bin/env python


class TriggerStage(object):
    def __init__(self, **kwargs):
        self.mask = 0
        self.value = 0
        self.delay = 0
        self.level = 0
        self.channel = 0
        self.serial = 0
        self.start = 0
        for kw in kwargs:
            setattr(self, kw, kwargs[kw])


class Settings(object):
    def __init__(self, **kwargs):
        self.clock_rate = 100000000
        self.timeout = None
        self.latest_first = True
        self.divider = 2
        self.read_count = 4096
        self.delay_count = 2048
        self.external = False
        self.inverted = False
        self.filter = False
        self.demux = False
        self.channel_groups = 0x0
        self.trigger_enable = 'None'
        self.trigger_stages = [
            TriggerStage(level=i) for i in xrange(self.trigger_max_stages)]

    @property
    def trigger_max_stages(self):
        return len(self.trigger_stages)

    @trigger_max_stages.setter
    def trigger_max_stages(self, n):
        self.trigger_stages = [TriggerStage(level=i) for i in xrange(n)]

    @property
    def sample_rate(self):
        rate = int(self.clock_rate / self.divider)
        if self.demux:
            rate *= 2
        return rate

    # TODO set properties for read and delay count to allow auto-calculation
