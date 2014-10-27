#!/usr/bin/env python

import cPickle as pickle


def save(capture, filename, settings=None, meta=None):
    d = {
        'data': capture,
        'settings': settings,
        'meta': meta,
    }
    with open(filename, 'w') as f:
        pickle.dump(d, f)
    return


def load(filename):
    with open(filename, 'r') as f:
        d = pickle.load(f)
    # parse out settings and data
    return d['data'], d.get('settings', None), d.get('meta', None)
