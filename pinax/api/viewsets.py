from __future__ import unicode_literals

import contextlib
import functools
import json
import logging
import traceback

from django.conf import settings
from django.conf.urls import url
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models.base import ModelBase
from django.http import HttpResponse, Http404
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt

from .exceptions import ErrorResponse, AuthenticationFailed, SerializationError
from .http import Response
from .jsonapi import TopLevel, Included


logger = logging.getLogger(__name__)


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
                endpoint = getattr(self, request.method.lower(), self.http_method_not_allowed)
            else:
                endpoint = self.http_method_not_allowed
            self.check_authentication(endpoint)
            self.prepare()
            self.check_permissions(endpoint)
            response = endpoint(request, *args, **kwargs)
            if not isinstance(response, HttpResponse):
                raise ValueError("view did not return an HttpResponse (got: {})".format(type(response)))
        except Exception as exc:
            response = self.handle_exception(exc)
        return response

    @property
    def debug(self):
        return settings.DEBUG or getattr(settings, "PINAX_API_DEBUG", False)

    def handle_exception(self, exc):
        if isinstance(exc, ErrorResponse):
            return exc.response
        elif isinstance(exc, Http404):
            return self.render_error(exc.args[0], status=404)
        else:
            logger.error("{}: {}".format(exc.__class__.__name__, str(exc)), exc_info=True)
            if self.debug:
                return self.render_error(
                    traceback.format_exc().splitlines()[-1],
                    status=500
                )
            else:
                return self.render_error("unknown server error", status=500)

    def get_pk(self):
        """
        Convenience method returning URL PK kwarg.
        """
        pk_url_kwarg = self.url.lookup["field"]
        return self.kwargs[pk_url_kwarg] if pk_url_kwarg in self.kwargs else None

    def get_resource_object_model(self):
        """
        Convenience method returning Resource's object model, if any.
        """
        if hasattr(self, "resource_class"):
            return self.resource_class.model if hasattr(self.resource_class, "model") else None
        else:
            return None

    def get_queryset(self):
        """
        Convenience method returning all Resource's object model objects.
        """
        return self.get_resource_object_model()._default_manager.all()

    def prepare(self):
        """
        Sets `self.obj` to a retrieved Resource object.

        No action is taken if requested method does not operate on single objects.

        No action is taken if EndpointSet.get_object_model_class()
        does not return a Django model.
        """
        # EndpointSets may use a different data storage than Django models.
        # Do not assume Django models are used.
        if isinstance(self.get_resource_object_model(), ModelBase):
            if self.requested_method in ["retrieve", "update", "destroy"]:
                self.pk = self.get_pk()
                self.obj = self.get_object_or_404(self.get_queryset(), pk=self.pk)

    def check_authentication(self, endpoint):
        user = None
        backends = []
        backends.extend(getattr(endpoint, "authentication", []))
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

    def check_permissions(self, endpoint):
        perms = []
        perms.extend(getattr(endpoint, "permissions", []))
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
            raise ErrorResponse(**self.error_response_kwargs(str(e), title="Invalid JSON", status=400))

    @contextlib.contextmanager
    def validate(self, resource_class, collection=False, obj=None):
        """
        Generator yields either a validated resource (collection=False)
        or a resource generator callable (collection=True).

        ValidationError exceptions resulting from subsequent (after yield)
        resource manipulation cause an immediate ErrorResponse.
        """
        data = self.parse_data()
        if "data" not in data:
            raise ErrorResponse(**self.error_response_kwargs('Missing "data" key in payload.', status=400))

        if collection and not isinstance(data["data"], list):
            raise ErrorResponse(**self.error_response_kwargs("Data must be in a list.", status=400))

        try:
            if collection:
                yield (self.validate_resource(resource_class, resource_data, obj) for resource_data in data["data"])
            else:
                yield self.validate_resource(resource_class, data["data"], obj)
        except ValidationError as exc:
            raise ErrorResponse(
                TopLevel.from_validation_error(exc, resource_class).serializable(),
                status=400,
            )

    def validate_resource(self, resource_class, resource_data, obj=None):
        """
        Validates resource data for a resource class.
        """
        if "attributes" not in resource_data:
            raise ErrorResponse(**self.error_response_kwargs('Missing "attributes" key in data.', status=400))
        resource = resource_class()
        resource.populate(resource_data, obj=obj)
        return resource

    def render(self, resource, **kwargs):
        try:
            payload = self.create_top_level(resource, **kwargs).serializable(request=self.request)
        except SerializationError as exc:
            return self.render_error(str(exc), status=400)
        else:
            return Response(payload, status=200)

    def render_create(self, resource, **kwargs):
        try:
            payload = self.create_top_level(resource, **kwargs).serializable(request=self.request)
        except SerializationError as exc:
            return self.render_error(str(exc), status=400)
        else:
            res = Response(payload, status=201)
            res["Location"] = resource.get_self_link(request=self.request)
            return res

    def render_delete(self):
        return Response({}, status=204)

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

    def create_top_level(self, resource, linkage=False, **kwargs):
        kwargs.update(
            {
                "data": resource,
                "links": True,
                "linkage": linkage,
            }
        )
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
