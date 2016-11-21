from __future__ import unicode_literals

from .registry import registry


class Relationship(object):

    def __init__(self, api_type, collection=False, attr=None):
        self.api_type = api_type
        self.collection = collection
        self.attr = attr

    def resource_class(self):
        return registry.get(self.api_type)
