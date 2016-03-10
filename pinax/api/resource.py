from __future__ import unicode_literals

import datetime

from functools import partial
from operator import attrgetter, itemgetter

from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db.models.query import ModelIterable

from . import rfc3339
from .exceptions import SerializationError
from .registry import registry


class Attribute(object):

    def __init__(self, name, obj_attr=None):
        self.name = name
        self.obj_attr = name if obj_attr is None else obj_attr


class ResourceIterable(ModelIterable):

    def __init__(self, resource_class, queryset):
        self.resource_class = resource_class
        super(ResourceIterable, self).__init__(queryset)

    def __iter__(self):
        for obj in super(ResourceIterable, self).__iter__():
            yield self.resource_class(obj)


class Resource(object):

    api_type = ""
    attributes = []
    relationships = {}
    bound_viewset = None

    @classmethod
    def from_queryset(cls, qs):
        return qs._clone(_iterable_class=partial(ResourceIterable, cls))

    @classmethod
    def populate(cls, data, obj=None):
        if obj is None:
            obj = cls.model()
        for k, v in data["attributes"].items():
            f = cls.model._meta.get_field(k)
            setattr(obj, f.attname, v)
        r = cls(obj)
        for k, v in data.get("relationships", {}).items():
            rel = cls.relationships[k]
            attr = rel.attr if rel.attr is not None else k
            if not rel.collection:
                f = cls.model._meta.get_field(attr)
                try:
                    o = f.rel.to._default_manager.get(pk=v["data"]["id"])
                except ObjectDoesNotExist:
                    raise ValidationError({
                        k: 'Relationship "{}" object ID {} does not exist'.format(
                            k, v["data"]["id"]
                        )
                    })
                setattr(obj, f.name, o)
            else:
                # A collection can be:
                #  * ManyToManyField
                #  * Reverse relation
                given = set(map(itemgetter("id"), v["data"]))
                f = cls.model._meta.get_field(attr)
                if f in cls.model._meta.related_objects:
                    related = f.field.model
                    accessor_name = f.get_accessor_name()
                else:
                    related = f.rel.model
                    accessor_name = f.name
                qs = related._default_manager.filter(pk__in=given)
                found = set(map(attrgetter("id"), qs))
                missing = given.difference(found)
                if missing:
                    raise ValidationError({
                        k: 'Relationship "{}" object IDs {} do not exist'.format(
                            k,
                            ", ".join(sorted(missing))
                        )
                    })

                def save(self, parent=None):
                    if parent is None:
                        parent = obj
                    getattr(parent, accessor_name).add(*qs)
                obj.save_relationships = save
        return r

    def __init__(self, obj):
        self.obj = obj

    def create(self, **kwargs):
        self.obj.full_clean()
        self.obj.save()
        return self.obj

    def update(self, **kwargs):
        self.obj.full_clean()
        self.obj.save()
        return self.obj

    def save(self, create_kwargs=None, update_kwargs=None):
        if create_kwargs is None:
            create_kwargs = {}
        if update_kwargs is None:
            update_kwargs = {}
        if self.obj.pk is None:
            self.obj = self.create(**create_kwargs)
        else:
            self.obj = self.update(**update_kwargs)

    def get_identifier(self):
        return {
            "type": self.api_type,
            "id": str(self.id),
        }

    def resolve_url_kwargs(self):
        assert hasattr(self, "viewset"), "resolve_url_kwargs requires a bound resource (got {}).".format(self)
        kwargs = {}
        viewset = self.viewset
        child_obj = None  # moving object as we traverse the ancestors
        while viewset is not None:
            if child_obj is None:
                obj = self.obj
            else:
                obj = getattr(child_obj, viewset.url.lookup["field"])
            kwargs[viewset.url.lookup["field"]] = viewset.resource_class(obj).id
            viewset, child_obj = viewset.parent, obj
        return kwargs

    def get_self_link(self, request=None):
        kwargs = self.resolve_url_kwargs()
        url = reverse("{}-detail".format(self.viewset.url.base_name), kwargs=kwargs)
        if request is not None:
            return request.build_absolute_uri(url)
        return url

    def get_self_relationship_link(self, related_name, request=None):
        kwargs = self.resolve_url_kwargs()
        url = reverse(
            "{}-{}-relationship-detail".format(
                self.viewset.url.base_name,
                related_name,
            ),
            kwargs=kwargs
        )
        if request is not None:
            return request.build_absolute_uri(url)
        return url

    def resolve_attr(self, attr):
        return resolve_value(getattr(self.obj, attr.obj_attr))

    def resolve_relationship(self, related_name, rel):
        return getattr(self.obj, related_name)

    def serialize(self, links=False, request=None):
        attributes = {}
        for attr in self.attributes:
            if isinstance(attr, str):
                attr = Attribute(name=attr)
            attributes[attr.name] = self.resolve_attr(attr)
        relationships = {}
        for name, rel in self.relationships.items():
            rel_obj = relationships.setdefault(name, {
                "links": {
                    "self": self.get_self_relationship_link(name, request=request),
                },
            })
            if rel.collection:
                qs = self.resolve_relationship(name, rel).all()
                rel_data = rel_obj.setdefault("data", [])
                for v in qs:
                    rel_data.append(rel.resource_class()(v).get_identifier())
            else:
                v = self.resolve_relationship(name, rel)
                if v is not None:
                    rel_obj["data"] = rel.resource_class()(v).get_identifier()
                else:
                    rel_obj["data"] = None
        data = {
            "attributes": attributes,
        }
        data.update(self.get_identifier())
        if links:
            data["links"] = {"self": self.get_self_link(request=request)}
        if relationships:
            data["relationships"] = relationships
        return data

    def serializable(self, linkage=False, included=None, **kwargs):
        data = {}
        if linkage:
            data.update(self.get_identifier())
        else:
            data.update(self.serialize(**kwargs))
        if included is not None:
            if linkage:
                included.add(registry.get(self.api_type)(self.obj))
            for path in included.paths:
                resolve_include(self, path, included)
        return data


def resolve_include(resource, path, included):
    try:
        head, rest = path.split(".", 1)
    except ValueError:
        head, rest = path, ""
    if head not in resource.relationships:
        raise SerializationError("'{}' is not a valid relationship to include".format(head))
    rel = resource.relationships[head]
    if rel.collection:
        for obj in getattr(resource.obj, head).all():
            r = rel.resource_class()(obj)
            if rest:
                resolve_include(r, rest, included)
            included.add(r)
    else:
        r = rel.resource_class()(getattr(resource.obj, head))
        included.add(r)


def resolve_value(value):
    if callable(value):
        value = resolve_value(value())
    if isinstance(value, datetime.datetime):
        return rfc3339.encode(value)
    if hasattr(value, "as_json"):
        value = value.as_json()
    return value
