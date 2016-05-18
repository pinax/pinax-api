from __future__ import unicode_literals


registry = {}
bound_registry = {}


def register(cls):
    registry[cls.api_type] = cls
    return cls


def bind(parent=None, resource=None):
    def wrapper(viewset):
        if parent is not None:
            viewset.parent = parent
            viewset.url.parent = parent.url
        if resource is not None:
            BoundResource = type(
                str("Bound{}".format(resource.__class__.__name__)),
                (resource,),
                {"viewset": viewset},
            )
            viewset.resource_class = BoundResource
            # override registry with bound resource (typically what we want)
            registry[resource.api_type] = BoundResource
        viewset.relationships = getattr(viewset, "relationships", {})
        return viewset
    return wrapper
