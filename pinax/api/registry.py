from __future__ import unicode_literals


registry = {}
bound_registry = {}


def register(cls):
    registry[cls.api_type] = cls

    def as_jsonapi(self):
        return cls(self).serialize()

    cls.model.as_jsonapi = as_jsonapi
    return cls


def bind(parent=None, resource=None):
    def wrapper(endpointset):
        if parent is not None:
            endpointset.parent = parent
            endpointset.url.parent = parent.url
        if resource is not None:
            BoundResource = type(
                str("Bound{}".format(resource.__class__.__name__)),
                (resource,),
                {"endpointset": endpointset},
            )
            endpointset.resource_class = BoundResource
            # override registry with bound resource (typically what we want)
            registry[resource.api_type] = BoundResource
        endpointset.relationships = getattr(endpointset, "relationships", {})
        return endpointset
    return wrapper
