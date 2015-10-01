#!/usr/bin/env python
"""
Capture
    data
    data by channel
    data by member
    data by group
    filters/operations
"""


class Capture(object):
    def __init__(self, data, settings):
        self.settings = settings
        self.raw = data
        self._parse_data()

    def _parse_data(self):
        # TODO
        self._data_by_sample = self.raw
        self._data_by_key = self.raw

    def __getitem__(self, key):
        if isinstance(key, int):
            print "_data_by_sample"
            return self._data_by_sample[key]
        elif isinstance(key, (str, unicode)):
            print "_data_by_key"
            return self._data_by_key[key]
        else:
            raise TypeError("Invalid __getitem__ type %s" % type(key))
