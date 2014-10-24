#!/usr/bin/env python


def big_endian(s4):
    '''Re-cast 4 bytes as 32-bit int, MSB first.'''
    return (ord(s4[0]) << 24) | (ord(s4[1]) << 16) | \
        (ord(s4[2]) << 8) | ord(s4[3])


def little_endian(s4):
    '''Re-cast 4 bytes as 32-bit int, LSB first.'''
    return (ord(s4[3]) << 24) | (ord(s4[2]) << 16) | \
        (ord(s4[1]) << 8) | ord(s4[0])


u1 = lambda i: ord(i.next())
u2 = lambda i: ord(i.next()) << 8
u3 = lambda i: ord(i.next()) << 16
u4 = lambda i: ord(i.next()) << 24

unpack_functions = {
    0b0000: lambda i: u1(i) | u2(i) | u3(i) | u4(i),
    0b0001: lambda i: u2(i) | u3(i) | u4(i),
    0b0010: lambda i: u1(i) | u3(i) | u4(i),
    0b0011: lambda i: u3(i) | u4(i),
    0b0100: lambda i: u1(i) | u2(i) | u4(i),
    0b0101: lambda i: u2(i) | u4(i),
    0b0110: lambda i: u1(i) | u4(i),
    0b0111: lambda i: u4(i),
    0b1000: lambda i: u1(i) | u2(i) | u3(i),
    0b1001: lambda i: u2(i) | u3(i),
    0b1010: lambda i: u1(i) | u3(i),
    0b1011: lambda i: u3(i),
    0b1100: lambda i: u1(i) | u2(i),
    0b1101: lambda i: u2(i),
    0b1110: lambda i: u1(i),
    0b1111: lambda i: 0,
}

chars_by_group = {
    0b0000: 4,
    0b0001: 3,
    0b0010: 3,
    0b0011: 2,
    0b0100: 3,
    0b0101: 2,
    0b0110: 2,
    0b0111: 1,
    0b1000: 3,
    0b1001: 2,
    0b1010: 2,
    0b1011: 1,
    0b1100: 2,
    0b1101: 1,
    0b1110: 1,
    0b1111: 0
}
