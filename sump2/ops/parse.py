#!/usr/bin/env python
"""
settings = {
    'address': (0, 16),
    'data': (16, 8),
    'litfin': 24,
    'litfout': 25,
    'sysr': 26,
    'systb': 27,
    'dbin': 28,
    'wr': 29,
    'memr': 30,
    'o2': 31,
}

if settings[key] is a tuple = (start bit, length)
if settings[key] is a single value = bit index
"""

import numpy


def unpack(data, spec):
    if isinstance(spec, (tuple, list)):
        if len(spec) != 2:
            raise ValueError("spec must be of len 2 [!=%s]" % (len(spec), ))
        start, length = spec
        return (data >> start) & (2 ** length - 1)
    elif isinstance(spec, dict):
        raise NotImplementedError("Complex unpacking not yet supported")
    else:
        return (data >> int(spec)) & 0b1


def parse(capture, settings=None, **kwargs):
    if settings is None:
        settings = {}
    settings.update(kwargs)
    c = numpy.array(capture, dtype='int64')  # to allow unsafe shifting
    dt = [(k, 'int64') for k in sorted(settings)]
    r = numpy.empty(len(c), dtype=dt)
    for k in settings:
        r[k] = unpack(c, settings[k])
    return r
