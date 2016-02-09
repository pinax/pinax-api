import urllib.parse

from collections import namedtuple

from django.core.paginator import Paginator
from django.db import models

from .exceptions import ErrorResponse
from .urls import as_absolute_url


class ResourceIdentifier(namedtuple("ResourceIdentifier", "type id")):

    __slots__ = ()

    def as_dict(self):
        return {"type": self.type, "id": self.id}


def get_resource_type(obj_class):
    if issubclass(obj_class, models.Model):
        return obj_class._meta.model_name
    return obj_class.jsonapi_resource_type


def get_resource_identifier(obj):
    return ResourceIdentifier(
        type=get_resource_type(obj.__class__),
        id=obj.get_jsonapi_identifier(),
    )


def document_from_queryset(qs, attributes, relationships=None, request=None):
    included = {}
    paginator = Paginator(qs, 100)
    if request is not None:
        if "page[number]" in request.GET:
            try:
                page_number = int(request.GET.get("page[number]", "1"))
            except ValueError:
                page = paginator.page(1)
            else:
                page = paginator.page(page_number)
        else:
            page = paginator.page(1)
    else:
        page = paginator.page(1)
    links = {
        "self": as_absolute_url(get_resource_type(qs.model), "list", request=request),
    }
    if page.has_previous():
        u = urllib.parse.urlparse(links["self"])
        q = urllib.parse.parse_qs(u.query)
        q["page[number]"] = str(page.previous_page_number())
        links["prev"] = urllib.parse.ParseResult(
            u.scheme,
            u.netloc,
            u.path,
            u.params,
            urllib.parse.urlencode(q),
            u.fragment,
        ).geturl()
    if page.has_next():
        u = urllib.parse.urlparse(links["self"])
        q = urllib.parse.parse_qs(u.query)
        q["page[number]"] = str(page.next_page_number())
        links["next"] = urllib.parse.ParseResult(
            u.scheme,
            u.netloc,
            u.path,
            u.params,
            urllib.parse.urlencode(q),
            u.fragment,
        ).geturl()
    doc = {
        "jsonapi": {"version": "1.0"},
        "data": [
            obj_as_resource(obj, attributes, relationships=relationships, included=included, request=request)
            for obj in page
        ],
        "links": links,
    }
    if included:
        doc["included"] = list(included.values())
    return doc


def document_from_obj(obj, attributes, relationships=None, request=None):
    included = {}
    doc = {
        "jsonapi": {"version": "1.0"},
        "data": obj_as_resource(obj, attributes, relationships=relationships, included=included, request=request)
    }
    if included:
        doc["included"] = list(included.values())
    return doc


def document_from_collection_relationship(parent, qs, related_name, attributes=None, relationships=None, request=None):
    included = {}
    doc = {
        "jsonapi": {"version": "1.0"},
    }
    doc.update(queryset_as_relationship(
        parent, qs, related_name,
        attributes=attributes,
        relationships=relationships,
        included=included,
        request=request,
    ))
    if included:
        doc["included"] = list(included.values())
    return doc


def document_from_obj_relationship(parent, obj, related_name, attributes=None, relationships=None, request=None):
    included = {}
    doc = {
        "jsonapi": {"version": "1.0"},
    }
    doc.update(obj_as_relationship(
        parent, obj, related_name,
        attributes=attributes,
        relationships=relationships,
        included=included,
        request=request,
    ))
    if included:
        doc["included"] = list(included.values())
    return doc


def resolve_value(value):
    if callable(value):
        value = resolve_value(value())
    if hasattr(value, "as_json"):
        value = value.as_json()
    return value


def obj_as_resource(obj, attributes, relationships=None, included=None, request=None):
    resid = get_resource_identifier(obj)
    res = {}
    res.update(resid.as_dict())
    for attribute in attributes:
        if isinstance(attribute, tuple):
            lookup, attr = attribute
        else:
            lookup, attr = attribute, attribute
        res.setdefault("attributes", {})[attr] = resolve_value(getattr(obj, lookup))
    if relationships is None:
        relationships = {}
    for related_name, relationship in relationships.items():
        value = getattr(obj, related_name)
        if relationship.collection:
            # @@@ ask the relationship how to resolve the queryset instead of
            # assuming .all().
            r = queryset_as_relationship(
                obj, value.all(), related_name,
                attributes=relationship.attributes,
                relationships=relationship.relationships,
                included=included,
                request=request,
            )
        else:
            r = obj_as_relationship(
                obj, value, related_name,
                attributes=relationship.attributes,
                relationships=relationship.relationships,
                included=included,
                request=request,
            )
        res.setdefault("relationships", {})[related_name] = r
    if hasattr(obj, "get_jsonapi_lookup"):
        res["links"] = {
            "self": as_absolute_url(
                get_resource_type(obj.__class__), "detail",
                kwargs=dict(obj.get_jsonapi_lookup()),
                request=request,
            ),
        }
    return res


def queryset_as_relationship(parent, qs, related_name, attributes=None, relationships=None, included=None, request=None):
    r = {}
    r["links"] = {
        "self": as_absolute_url(
            get_resource_type(parent.__class__), "list",
            related_name=related_name,
            relationship=True,
            kwargs=dict(parent.get_jsonapi_lookup()),
            request=request,
        ),
    }
    data = r.setdefault("data", [])
    for obj in qs:
        resid = get_resource_identifier(obj)
        data.append(resid.as_dict())
        if included is not None and attributes:
            included[resid] = obj_as_resource(
                obj, attributes,
                relationships=relationships,
                included=included,
                request=request,
            )
    return r


def obj_as_relationship(parent, obj, related_name, attributes=None, relationships=None, included=None, request=None):
    r = {}
    r["links"] = {
        "self": as_absolute_url(
            get_resource_type(parent.__class__), "detail",
            related_name=related_name,
            relationship=True,
            kwargs=dict(parent.get_jsonapi_lookup()),
            request=request,
        ),
    }
    resid = get_resource_identifier(obj)
    r["data"] = resid.as_dict()
    if included is not None and attributes:
        included[resid] = obj_as_resource(
            obj, attributes,
            relationships=relationships,
            included=included,
            request=request,
        )
    return r


def response_for_validation_error(exc, model):
    data = {"errors": []}
    for field, errors in exc:
        if field != "__all__":
            f = model._meta.get_field(field)
        else:
            f = None
        for err in errors:
            if f is None:
                pointer = "/data"
            elif isinstance(f, models.ForeignKey):
                pointer = "/data/relationships/{}"
            else:
                pointer = "/data/attributes/{}"
            data["errors"].append({
                "status": "400",
                "detail": err,
                "source": {
                    "pointer": pointer.format(field),
                },
            })
    return ErrorResponse(data, status=400)
