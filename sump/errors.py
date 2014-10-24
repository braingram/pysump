#!/usr/bin/env python


class SumpError (StandardError):
    '''Errors raised by the SUMP client.'''


class SumpIdError (SumpError):
    '''The wrong string was returned by an ID request.'''


class SumpFlagsError (SumpError):
    '''Illegal combination of flags.'''


class SumpTriggerEnableError (SumpError):
    '''Illegal trigger enable setting.'''


class SumpStageError (SumpError):
    '''Illegal trigger stage setting.'''
