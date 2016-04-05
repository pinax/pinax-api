from __future__ import unicode_literals

try:
    from collections import abc
except ImportError:
    import collections as abc

from django.core.paginator import Paginator
from django.utils.six.moves.urllib.parse import (
    urlparse, parse_qs, urlencode, ParseResult
)

from .resource import Resource


class Included(set):

    def __init__(self, paths):
        self.paths = paths
        super(Included, self).__init__()


class TopLevel:

    @classmethod
    def from_validation_error(cls, exc, resource_class):
        errs = []
        for field, errors in exc:
            for err in errors:
                if field == "__all__":
                    pointer = "/data"
                elif field in resource_class.relationships:
                    pointer = "/data/relationships/{}"
                else:
                    pointer = "/data/attributes/{}"
                err = {
                    "status": "400",
                    "detail": err,
                    "source": {
                        "pointer": pointer.format(field),
                    },
                }
                errs.append(err)
        return cls(errors=errs)

    def __init__(self, data=None, errors=None, links=False, included=None, meta=None, linkage=False):
        self.data = data
        self.errors = errors
        self.links = links
        self.included = included
        self.meta = meta
        self.linkage = linkage

        # internal state
        self._current_page = None

    def get_serializable_data(self, request=None):
        if isinstance(self.data, abc.Iterable):
            ret = []
            data = self.data
            if request is not None:
                paginator = Paginator(data, 100)
                if "page[number]" in request.GET:
                    try:
                        page_number = int(request.GET.get("page[number]", "1"))
                    except ValueError:
                        page = paginator.page(1)
                    else:
                        page = paginator.page(page_number)
                else:
                    page = paginator.page(1)
                self._current_page = data = page
            for x in data:
                ret.append(x.serializable(
                    links=self.links,
                    linkage=self.linkage,
                    included=self.included,
                    request=request,
                ))
            return ret
        elif isinstance(self.data, Resource):
            return self.data.serializable(
                links=self.links,
                linkage=self.linkage,
                included=self.included,
                request=request,
            )
        else:
            return self.data

    def build_links(self, request=None):
        links = {}
        if request is not None:
            page = self._current_page
            links["self"] = request.build_absolute_uri(request.path)
            if page.has_previous():
                u = urlparse(links["self"])
                q = parse_qs(u.query)
                q["page[number]"] = str(page.previous_page_number())
                links["prev"] = ParseResult(
                    u.scheme,
                    u.netloc,
                    u.path,
                    u.params,
                    urlencode(q),
                    u.fragment,
                ).geturl()
            if page.has_next():
                u = urlparse(links["self"])
                q = parse_qs(u.query)
                q["page[number]"] = str(page.next_page_number())
                links["next"] = ParseResult(
                    u.scheme,
                    u.netloc,
                    u.path,
                    u.params,
                    urlencode(q),
                    u.fragment,
                ).geturl()
        return links

    def serializable(self, request=None):
        res = {"jsonapi": {"version": "1.0"}}
        if self.data is not None:
            res.update(dict(data=self.get_serializable_data(request=request)))
        if self.errors is not None:
            res.update(dict(errors=self.errors))
        if self.included:
            res.update(dict(included=[r.serializable(links=self.links, request=request) for r in self.included]))
        if self.meta is not None:
            res.update(dict(meta=self.meta))
        if self.links:
            res.update(dict(links=self.build_links(request=request)))
        return res
