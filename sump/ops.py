#!/usr/bin/env python


def big_endian(s4):
    '''Re-cast 4 bytes as 32-bit int, MSB first.'''
    return (ord(s4[0]) << 24) | (ord(s4[1]) << 16) | \
        (ord(s4[2]) << 8) | ord(s4[3])


def little_endian(s4):
    '''Re-cast 4 bytes as 32-bit int, LSB first.'''
    return (ord(s4[3]) << 24) | (ord(s4[2]) << 16) | \
        (ord(s4[1]) << 8) | ord(s4[0])
