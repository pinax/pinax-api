from __future__ import unicode_literals

import contextlib
import functools
import json
import traceback

from django.conf import settings
from django.conf.urls import url
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.http import HttpResponse, Http404
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt

from .exceptions import ErrorResponse, AuthenticationFailed, SerializationError
from .http import Response
from .jsonapi import TopLevel, Included


class EndpointSet(View):

    @classmethod
    def as_view(cls, **initkwargs):
        view_mapping_kwargs = initkwargs.pop("view_mapping_kwargs", {})
        view = super(EndpointSet, cls).as_view(**initkwargs)

        def view(request, *args, **kwargs):
            self = cls(**initkwargs)
            mapping = cls.view_mapping(**view_mapping_kwargs)
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
            self.check_authentication(handler)
            self.prepare()
            self.check_permissions(handler)
            response = handler(request, *args, **kwargs)
            if not isinstance(response, HttpResponse):
                raise ValueError("view did not return an HttpResponse (got: {})".format(type(response)))
        except Exception as exc:
            response = self.handle_exception(exc)
        return response

    def handle_exception(self, exc):
        if isinstance(exc, ErrorResponse):
            return exc.response
        elif isinstance(exc, Http404):
            return self.render_error(exc.args[0], status=404)
        else:
            if not settings.DEBUG:
                traceback.print_exc()
                return self.render_error(
                    traceback.format_exc().splitlines()[-1],
                    status=500
                )
            else:
                return self.render_error("unknown server error", status=500)

    def prepare(self):
        pass

    def check_authentication(self, handler):
        user = None
        backends = []
        backends.extend(getattr(handler, "authentication", []))
        backends.extend(getattr(self, "middleware", {}).get("authentication", []))
        for backend in backends:
            try:
                user = backend.authenticate(self.request)
            except AuthenticationFailed as exc:
                raise ErrorResponse(**self.error_response_kwargs(str(exc), status=401))
            if user:
                self.request.user = user
                break
        else:
            if not self.request.user.is_authenticated():
                raise ErrorResponse(**self.error_response_kwargs("Authentication Required.", status=401))

    def check_permissions(self, handler):
        perms = []
        perms.extend(getattr(handler, "permissions", []))
        perms.extend(getattr(self, "middleware", {}).get("permissions", []))
        for perm in perms:
            res = perm(self.request, view=self)
            if res is None:
                continue
            if isinstance(res, tuple):
                ok, status, msg = res
            else:
                ok, status, msg = res, 403, "Permission Denied."
            if not ok:
                raise ErrorResponse(**self.error_response_kwargs(msg, status=status))

    def parse_data(self):
        # @@@ this method is not the most ideal implementation generally, but
        # until a better design comes along, we roll with it!
        try:
            return json.loads(self.request.body.decode(settings.DEFAULT_CHARSET))
        except json.JSONDecodeError as e:
            raise ErrorResponse(**self.error_kwargs(str(e), title="Invalid JSON", status=400))

    @contextlib.contextmanager
    def validate(self, resource_class, obj=None):
        data = self.parse_data()
        if "data" not in data:
            raise ErrorResponse(**self.error_kwargs('Missing "data" key in payload.', status=400))
        if "attributes" not in data["data"]:
            raise ErrorResponse(**self.error_kwargs('Missing "attributes" key in data.', status=400))
        resource = resource_class()
        try:
            resource.populate(data["data"], obj=obj)
            yield resource
        except ValidationError as exc:
            raise ErrorResponse(
                TopLevel.from_validation_error(exc, resource_class).serializable(),
                status=400,
            )

    def render(self, resource, meta=None):
        try:
            payload = self.create_top_level(resource, meta=meta).serializable(request=self.request)
        except SerializationError as exc:
            return self.render_error(str(exc), status=400)
        else:
            return Response(payload, status=200)

    def render_create(self, resource, meta=None):
        try:
            payload = self.create_top_level(resource, meta=meta).serializable(request=self.request)
        except SerializationError as exc:
            return self.render_error(str(exc), status=400)
        else:
            res = Response(payload, status=201)
            res["Location"] = resource.get_self_link(request=self.request)
            return res

    def render_delete(self):
        return Response({}, status=200)

    def error_response_kwargs(self, message, title=None, status=400, extra=None):
        if extra is None:
            extra = {}
        err = dict(extra)
        err.update({
            "status": str(status),
            "detail": message,
        })
        if title is not None:
            err["title"] = title
        return {
            "data": TopLevel(errors=[err]).serializable(),
            "status": status,
        }

    def render_error(self, *args, **kwargs):
        return Response(**self.error_response_kwargs(*args, **kwargs))

    def get_object_or_404(self, qs, **kwargs):
        try:
            return qs.get(**kwargs)
        except ObjectDoesNotExist:
            raise Http404("{} does not exist.".format(qs.model._meta.verbose_name.capitalize()))

    def create_top_level(self, resource, linkage=False, meta=None):
        kwargs = {
            "data": resource,
            "meta": meta,
            "links": True,
            "linkage": linkage,
        }
        if "include" in self.request.GET:
            kwargs["included"] = Included(self.request.GET["include"].split(","))
        return TopLevel(**kwargs)


class ResourceEndpointSet(EndpointSet):

    parent = None

    @classmethod
    def view_mapping(cls, collection):
        if collection:
            mapping = {
                "get": "list",
                "post": "create",
            }
        else:
            mapping = {
                "get": "retrieve",
                "patch": "update",
                "delete": "destroy",
            }
        return mapping

    @classmethod
    def as_urls(cls):
        urls = [
            url(
                r"^{}$".format(cls.url.collection_regex()),
                cls.as_view(view_mapping_kwargs=dict(collection=True)),
                name="{}-list".format(cls.url.base_name)
            ),
            url(
                r"^{}$".format(cls.url.detail_regex()),
                cls.as_view(view_mapping_kwargs=dict(collection=False)),
                name="{}-detail".format(cls.url.base_name)
            )
        ]
        for related_name, eps in cls.relationships.items():
            urls.extend(eps.as_urls(cls.url, related_name))
        return urls


class RelationshipEndpointSet(EndpointSet):

    @classmethod
    def view_mapping(cls):
        return {
            "get": "retrieve",
            "post": "create",
            "patch": "update",
            "delete": "destroy",
        }

    @classmethod
    def as_urls(cls, base_url, related_name):
        urls = [
            url(
                r"^{}/relationships/{}$".format(
                    base_url.detail_regex(),
                    related_name,
                ),
                cls.as_view(),
                name="-".join([base_url.base_name, related_name, "relationship", "detail"])
            ),
        ]
        return urls

    def create_top_level(self, *args, **kwargs):
        kwargs["linkage"] = True
        return super(RelationshipEndpointSet, self).create_top_level(*args, **kwargs)
