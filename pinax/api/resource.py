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

    def __init__(self, name, obj_attr=None, scope="rw"):
        self.name = name
        self.obj_attr = name if obj_attr is None else obj_attr
        self.scope = scope


class ResourceIterable(ModelIterable):

    def __init__(self, resource_class, queryset):
        self.resource_class = resource_class
        super(ResourceIterable, self).__init__(queryset)

    def __iter__(self):
        for obj in super(ResourceIterable, self).__iter__():
            yield self.resource_class(obj)


empty = object()


def scoped(iterable, scope):
    for attr in iterable:
        if isinstance(attr, str):
            attr = Attribute(name=attr)
        if scope in attr.scope:
            yield attr


class Resource(object):

    api_type = ""
    attributes = []
    relationships = {}
    bound_viewset = None

    @classmethod
    def from_queryset(cls, qs):
        return qs._clone(_iterable_class=partial(ResourceIterable, cls))

    def __init__(self, obj=None):
        self.obj = obj

    def populate(self, data, obj=None):
        if obj is None:
            obj = self.model()
        self.obj = obj
        for attr in scoped(self.attributes, "w"):
            value = data["attributes"].get(attr.name, empty)
            if value is not empty:
                self.set_attr(attr, value)
        for related_name, rel in self.relationships.items():
            value = data.get("relationships", {}).get(related_name, empty)
            if value is not empty:
                self.set_relationship(related_name, rel, value)

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

    def get_attr(self, attr):
        if hasattr(self, attr.obj_attr):
            value = getattr(self, attr.obj_attr)
        else:
            value = getattr(self.obj, attr.obj_attr)
        return resolve_value(value)

    def get_relationship(self, related_name, rel):
        return getattr(self.obj, related_name)

    def set_attr(self, attr, value):
        setattr(self.obj, attr.obj_attr, value)

    def set_relationship(self, related_name, rel, value):
        attr = rel.attr if rel.attr is not None else related_name
        if not rel.collection:
            f = self.model._meta.get_field(attr)
            try:
                o = f.rel.to._default_manager.get(pk=value["data"]["id"])
            except ObjectDoesNotExist:
                raise ValidationError({
                    related_name: 'Relationship "{}" object ID {} does not exist'.format(
                        related_name, value["data"]["id"]
                    )
                })
            setattr(self.obj, related_name, o)
        else:
            # A collection can be:
            #  * ManyToManyField
            #  * Reverse relation
            given = set(map(itemgetter("id"), value["data"]))
            f = self.model._meta.get_field(attr)
            if f in self.model._meta.related_objects:
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
                    related_name: 'Relationship "{}" object IDs {} do not exist'.format(
                        related_name,
                        ", ".join(sorted(missing))
                    )
                })

            def save(self, parent=None):
                if parent is None:
                    parent = self.obj
                getattr(parent, accessor_name).add(*qs)
            self.obj.save_relationships = save

    def serialize(self, links=False, request=None):
        attributes = {}
        for attr in scoped(self.attributes, "r"):
            attributes[attr.name] = self.get_attr(attr)
        relationships = {}
        for name, rel in self.relationships.items():
            rel_obj = relationships.setdefault(name, {
                "links": {
                    "self": self.get_self_relationship_link(name, request=request),
                },
            })
            if rel.collection:
                qs = self.get_relationship(name, rel).all()
                rel_data = rel_obj.setdefault("data", [])
                for v in qs:
                    rel_data.append(rel.resource_class()(v).get_identifier())
            else:
                v = self.get_relationship(name, rel)
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
