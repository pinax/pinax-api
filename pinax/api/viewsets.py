from __future__ import unicode_literals

import collections
import contextlib
import functools
import itertools
import json

from django.conf import settings
from django.conf.urls import url
from django.core.exceptions import ValidationError
from django.db import models
from django.http import Http404
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt

from . import jsonapi
from .exceptions import ErrorResponse
from .http import Response
from .jsonapi import response_for_validation_error


ResourceURL = collections.namedtuple(
    "ResourceURL", [
        "base_regex",
        "lookup_field",
        "lookup_regex",
        "base_name"
    ],
)


class ViewSet(View):

    parent_viewset = None
    related_name = ""
    relationships = None

    @classmethod
    def as_view(cls, **initkwargs):
        collection = initkwargs.pop("collection", False)
        view = super(ViewSet, cls).as_view(**initkwargs)

        def view(request, *args, **kwargs):
            self = cls(**initkwargs)
            if collection:
                if self.related_name:
                    mapping = {
                        "get": "list_{}_relationship".format(self.related_name),
                        "post": "create_{}_relationship".format(self.related_name),
                    }
                else:
                    mapping = {
                        "get": "list",
                        "post": "create",
                    }
            else:
                if self.related_name:
                    mapping = {
                        "get": "retrieve_{}_relationship".format(self.related_name),
                    }
                else:
                    mapping = {
                        "get": "retrieve",
                        "patch": "update",
                        "delete": "destroy",
                    }
            for verb, method in mapping.items():
                if hasattr(self, method):
                    setattr(self, verb, getattr(self, method))
            self.requested_method = mapping.get(request.method.lower())
            self.args = args
            self.kwargs = kwargs
            self.request = request
            return self.dispatch(request, *args, **kwargs)

        functools.update_wrapper(view, cls, updated=())
        functools.update_wrapper(view, cls.dispatch, assigned=())
        return csrf_exempt(view)

    def dispatch(self, request, *args, **kwargs):
        try:
            if request.method.lower() in self.http_method_names:
                handler = getattr(self, request.method.lower(), self.http_method_not_allowed)
            else:
                handler = self.http_method_not_allowed
            response = handler(request, *args, **kwargs)
        except Exception as exc:
            response = self.handle_exception(exc)
        return response

    def handle_exception(self, exc):
        if isinstance(exc, ErrorResponse):
            return exc.response
        elif isinstance(exc, Http404):
            data = {
                "errors": [
                    {
                        "status": "404",
                        "detail": exc.args[0],
                    },
                ],
            }
            return Response(data, status=404)
        else:
            raise

    def get_data(self, request):
        # @@@ this method is not the most ideal implementation generally, but
        # until a better design comes along, we roll with it!
        try:
            return json.loads(request.body.decode(settings.DEFAULT_CHARSET))
        except json.JSONDecodeError as e:
            data = {
                "errors": [{
                    "status": "400",
                    "title": "invalid JSON",
                    "detail": str(e),
                }],
            }
            raise ErrorResponse(data, status=400)

    @contextlib.contextmanager
    def validate(self, request, model, obj=None):
        data = self.get_data(request)
        if obj is None:
            obj = model()
        pairs = itertools.chain(
            data["data"]["attributes"].items(),
            data["data"]["relationships"].items(),
        )
        for k, v in pairs:
            f = model._meta.get_field(k)
            if isinstance(f, models.ForeignKey):
                setattr(obj, f.attname, v["data"]["id"])
            else:
                setattr(obj, f.attname, v)
        try:
            yield obj
        except ValidationError as exc:
            raise response_for_validation_error(exc, model=model)

    def render(self, obj, **kwargs):
        if isinstance(obj, models.QuerySet):
            return Response(jsonapi.document_from_queryset(
                obj,
                request=self.request,
                **kwargs
            ))
        return Response(jsonapi.document_from_obj(
            obj,
            request=self.request,
            **kwargs
        ))

    def render_collection_relationship(self, parent, qs, **kwargs):
        return Response(jsonapi.document_from_collection_relationship(
            parent, qs, self.related_name,
            request=self.request, **kwargs
        ))

    def render_obj_relationship(self, parent, obj, **kwargs):
        return Response(jsonapi.document_from_obj_relationship(
            parent, obj, self.related_name,
            request=self.request, **kwargs
        ))


class ResourceViewSet(ViewSet):

    @classmethod
    def as_urls(cls, **kwargs):
        base_regex = r"^{}".format(cls.url.base_regex)
        urls = [
            url(
                r"{}/$".format(base_regex),
                cls.as_view(collection=True),
                name="{}-list".format(cls.url.base_name)
            ),
            url(
                r"{}/(?P<{}>{})/$".format(
                    base_regex,
                    cls.url.lookup_field,
                    cls.url.lookup_regex,
                ),
                cls.as_view(),
                name="{}-detail".format(cls.url.base_name)
            )
        ]
        relationships = {} if cls.relationships is None else cls.relationships
        for related_name, relationship in relationships.items():
            view_kwargs = {
                "parent_viewset": cls,
                "related_name": related_name,
            }
            url_name = [cls.url.base_name, related_name, "relationship"]
            if relationship.collection:
                url_name.append("list")
            else:
                url_name.append("detail")
            urls.extend([
                url(
                    r"{}/(?P<{}>{})/relationships/{}/$".format(
                        base_regex,
                        cls.url.lookup_field,
                        cls.url.lookup_regex,
                        related_name,
                    ),
                    cls.as_view(**dict(
                        view_kwargs,
                        collection=relationship.collection,
                        related_name=related_name,
                    )),
                    name="-".join(url_name),
                )
            ])
        return urls
