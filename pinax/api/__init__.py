import pkg_resources


default_app_config = "pinax.api.apps.AppConfig"
__version__ = pkg_resources.get_distribution("pinax-api").version


from . import authentication, permissions  # noqa
from .http import Response, Redirect  # noqa
from .registry import register, bind, registry  # noqa
from .relationships import Relationship  # noqa
from .resource import Resource, Attribute  # noqa
from .test import TestCase  # noqa
from .urls import URL as url, handler404  # noqa
from .viewsets import ResourceEndpointSet, RelationshipEndpointSet  # noqa
