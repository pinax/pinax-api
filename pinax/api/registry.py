from __future__ import unicode_literals


registry = {}


def register(cls):
    registry[cls.api_type] = cls
    return cls
