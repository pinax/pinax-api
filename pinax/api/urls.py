from __future__ import unicode_literals

from .http import Response
from .jsonapi import TopLevel


def handler404(request):
    return Response(TopLevel(errors=[{"status": "404"}]), status=404)


class URL(object):

    def __init__(self, base_name, base_regex, lookup, parent=None):
        self._base_name = base_name
        self.base_regex = base_regex
        self.lookup = lookup
        self.parent = parent

    @property
    def base_name(self):
        parts = []
        if self.parent is not None:
            parts.append(self.parent.base_name)
        parts.append(self._base_name)
        return "-".join(parts)

    def collection_regex(self, trailing_slash=False):
        parts = []
        if self.parent is not None:
            parts.append(self.parent.detail_regex(trailing_slash=True))
        parts.append(self.base_regex)
        if trailing_slash:
            parts.append("/")
        return "".join(parts)

    def detail_regex(self, trailing_slash=False):
        parts = []
        parts.append(r"{}/(?P<{}>{})".format(
            self.collection_regex(trailing_slash=False),
            self.lookup["field"],
            self.lookup["regex"],
        ))
        if trailing_slash:
            parts.append("/")
        return "".join(parts)
