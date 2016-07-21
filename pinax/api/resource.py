from __future__ import unicode_literals

import collections
import datetime

from collections import namedtuple
from functools import partial
from operator import attrgetter, itemgetter

from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.urlresolvers import reverse, NoReverseMatch
from django.db.models.query import ModelIterable

from . import rfc3339
from .exceptions import SerializationError


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


class Identifier(namedtuple("Identifier", "type id")):

    def __getitem__(self, key):
        if key == "type":
            return self.type
        if key == "id":
            return self.id
        return super(Identifier, self).__getitem__(key)

    def as_dict(self):
        return {"type": self.type, "id": self.id}


class Resource(object):

    api_type = ""
    attributes = []
    relationships = {}
    bound_endpointset = None

    @classmethod
    def from_queryset(cls, qs):
        return qs._clone(_iterable_class=partial(ResourceIterable, cls))

    def __init__(self, obj=None):
        self.obj = obj
        self.meta = {}

    def __hash__(self):
        return hash(self.identifier)

    def __eq__(self, other):
        return self.identifier == other.identifier

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

    @property
    def identifier(self):
        return Identifier(type=self.api_type, id=str(self.id))

    def resolve_url_kwargs(self):
        assert hasattr(self, "endpointset"), "resolve_url_kwargs requires a bound resource (got {}).".format(self)
        kwargs = {}
        endpointset = self.endpointset
        child_obj = None  # moving object as we traverse the ancestors
        while endpointset is not None:
            if child_obj is None:
                obj = self.obj
            else:
                obj = getattr(child_obj, endpointset.url.lookup["field"])
            if endpointset.url.lookup is not None:
                kwargs[endpointset.url.lookup["field"]] = endpointset.resource_class(obj).id
            endpointset, child_obj = endpointset.parent, obj
        return kwargs

    def get_self_link(self, request=None):
        kwargs = self.resolve_url_kwargs()
        url = reverse("{}-detail".format(self.endpointset.url.base_name), kwargs=kwargs)
        if request is not None and hasattr(request, "build_absolute_uri"):
            return request.build_absolute_uri(url)
        return url

    def get_self_relationship_link(self, related_name, request=None):
        kwargs = self.resolve_url_kwargs()
        try:
            url = reverse(
                "{}-{}-relationship-detail".format(
                    self.endpointset.url.base_name,
                    related_name,
                ),
                kwargs=kwargs
            )
        except NoReverseMatch:
            return None
        if request is not None and hasattr(request, "build_absolute_uri"):
            return request.build_absolute_uri(url)
        return url

    def get_attr(self, attr):
        if hasattr(self, attr.obj_attr):
            value = getattr(self, attr.obj_attr)
        else:
            value = getattr(self.obj, attr.obj_attr)
        return resolve_value(value)

    def get_relationship(self, related_name, rel):
        if rel.collection:
            iterator = getattr(self.obj, related_name)
            if not isinstance(iterator, collections.Iterable):
                if not hasattr(iterator, "all"):
                    raise TypeError("Relationship {} must be iterable or QuerySet".format(related_name))
                else:
                    iterator = iterator.all()
            return iterator
        else:
            return getattr(self.obj, related_name)

    def set_attr(self, attr, value):
        if hasattr(self, attr.obj_attr):
            setattr(self, attr.obj_attr, value)
        else:
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
            rel_links = {}
            rel_self_link = self.get_self_relationship_link(name, request=request)
            if rel_self_link:
                rel_links["self"] = rel_self_link
            rel_initial = {}
            if rel_links:
                rel_initial["links"] = rel_links
            rel_obj = relationships.setdefault(name, rel_initial)
            if rel.collection:
                iterable = self.get_relationship(name, rel)
                rel_data = rel_obj.setdefault("data", [])
                for v in iterable:
                    rel_data.append(rel.resource_class()(v).identifier.as_dict())
            else:
                v = self.get_relationship(name, rel)
                if v is not None:
                    rel_obj["data"] = rel.resource_class()(v).identifier.as_dict()
                else:
                    rel_obj["data"] = None
        data = {
            "attributes": attributes,
        }
        data.update(self.identifier.as_dict())
        meta = {}
        meta.update(self.meta)
        if meta:
            data["meta"] = meta
        if links:
            data["links"] = {"self": self.get_self_link(request=request)}
        if relationships:
            data["relationships"] = relationships
        return data

    def serializable(self, linkage=False, included=None, **kwargs):
        data = {}
        if linkage:
            data.update(self.identifier.as_dict())
        else:
            data.update(self.serialize(**kwargs))
        if included is not None:
            if linkage:
                included.add(self)
            for path in included.paths:
                resolve_include(self, path, included)
        return data


def resolve_include(resource, path, included):
    if path == "self":
        return
    try:
        head, rest = path.split(".", 1)
    except ValueError:
        head, rest = path, ""
    if head not in resource.relationships:
        raise SerializationError("'{}' is not a valid relationship to include".format(head))
    rel = resource.relationships[head]
    if rel.collection:
        for obj in resource.get_relationship(head, rel):
            r = rel.resource_class()(obj)
            if rest:
                resolve_include(r, rest, included)
            included.add(r)
    else:
        r = rel.resource_class()(resource.get_relationship(head, rel))
        included.add(r)


def resolve_value(value):
    if callable(value):
        value = resolve_value(value())
    if isinstance(value, datetime.datetime):
        value = rfc3339.encode(value)
    if isinstance(value, datetime.date):
        value = datetime.date.isoformat(value)
    if hasattr(value, "as_json"):
        value = value.as_json()
    return value
