from __future__ import unicode_literals

import contextlib
import functools
import json
import traceback

from django.conf import settings
from django.conf.urls import url
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.http import Http404
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt

from .exceptions import ErrorResponse, AuthenticationFailed, SerializationError
from .http import Response
from .jsonapi import TopLevel


def bind(parent=None, resource=None):
    def wrapper(viewset):
        if parent is not None:
            viewset.parent = parent
            viewset.url.parent = parent.url
        if resource is not None:
            class BoundResource(resource):
                bound_viewset = viewset
            viewset.resource_class = BoundResource
        return viewset
    return wrapper


class ResourceViewSet(View):

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
    def as_view(cls, **initkwargs):
        collection = initkwargs.pop("collection", False)
        view = super(ResourceViewSet, cls).as_view(**initkwargs)

        def view(request, *args, **kwargs):
            self = cls(**initkwargs)
            mapping = cls.view_mapping(collection)
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
            self.check_authentication()
            self.check_permissions()
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
            return self.render_error(exc.args[0], status=404)
        else:
            if settings.DEBUG:
                traceback.print_exc()
                return self.render_error(
                    traceback.format_exc().splitlines()[-1],
                    status=500
                )
            else:
                return self.render_error("unknown server error", status=500)

    def check_authentication(self):
        for backend in getattr(self, "middleware", {}).get("authentication", []):
            try:
                user = backend.authenticate(self.request)
            except AuthenticationFailed as exc:
                raise ErrorResponse(**self.error_response_kwargs(str(exc), status=401))
            if user:
                break
        else:
            raise ErrorResponse(**self.error_response_kwargs("Authentication Required.", status=401))
        self.request.user = user

    def check_permissions(self):
        for perm in getattr(self, "middleware", {}).get("permissions", []):
            res = perm(self.request)
            if isinstance(res, tuple):
                ok, status, msg = res
            else:
                ok, status = res, 403, "Permission Denied."
            if not ok:
                raise ErrorResponse(**self.error_response_kwargs(msg, status=status))

    def get_object_or_404(self, qs, **kwargs):
        try:
            return qs.get(**kwargs)
        except ObjectDoesNotExist:
            raise Http404("{} does not exist.".format(qs.model._meta.verbose_name.capitalize()))

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
        try:
            yield resource_class.populate(data["data"], obj=obj)
        except ValidationError as exc:
            raise ErrorResponse(
                TopLevel.from_validation_error(self.request, exc, resource_class).serializable(request=self.request),
                status=400,
            )

    def render(self, resource, meta=None):
        top_level = TopLevel(self.request, data=resource, meta=meta)
        try:
            payload = top_level.serializable(request=self.request)
        except SerializationError as exc:
            return self.render_error(str(exc), status=400)
        else:
            return Response(payload, status=200)

    def render_create(self, resource, meta=None):
        top_level = TopLevel(self.request, data=resource, meta=meta)
        try:
            payload = top_level.serializable(request=self.request)
        except SerializationError as exc:
            return self.render_error(str(exc), status=400)
        else:
            res = Response(payload, status=201)
            res["Location"] = self.request.build_absolute_uri(resource.get_self_link())
            return res

    def render_delete(self):
        pass

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
        return {"data": TopLevel(self.request, errors=[err]).serializable(request=self.request), "status": status}

    def render_error(self, *args, **kwargs):
        return Response(**self.error_response_kwargs(*args, **kwargs))

    @classmethod
    def as_urls(cls):
        urls = [
            url(
                r"^{}$".format(cls.url.collection_regex()),
                cls.as_view(collection=True),
                name="{}-list".format(cls.url.base_name)
            ),
            url(
                r"^{}$".format(cls.url.detail_regex()),
                cls.as_view(),
                name="{}-detail".format(cls.url.base_name)
            )
        ]
        return urls
