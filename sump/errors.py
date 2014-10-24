#!/usr/bin/env python


class SumpError(StandardError):
    '''Errors raised by the SUMP client.'''


class IdError(SumpError):
    '''The wrong string was returned by an ID request.'''


class FlagsError(SumpError):
    '''Illegal combination of flags.'''


class TriggerEnableError(SumpError):
    '''Illegal trigger enable setting.'''


class StageError(SumpError):
    '''Illegal trigger stage setting.'''


class SettingError(SumpError):
    '''Setting related error'''
