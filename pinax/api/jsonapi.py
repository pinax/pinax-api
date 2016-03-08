from __future__ import unicode_literals

from collections import abc

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

    def __init__(self, data=None, errors=None, links=False, included=None, meta=None):
        self.data = data
        self.errors = errors
        self.links = links
        self.included = included
        self.meta = meta

    def get_serializable_data(self, request=None):
        if isinstance(self.data, abc.Iterable):
            ret = []
            for x in self.data:
                ret.append(x.serializable(links=self.links, included=self.included, request=request))
            return ret
        elif isinstance(self.data, Resource):
            return self.data.serializable(links=self.links, included=self.included, request=request)
        else:
            return self.data

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
            res.update(dict(links={"self": request.build_absolute_uri(request.path)}))
        return res
