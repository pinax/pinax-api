import pkg_resources


default_app_config = "pinax.api.apps.AppConfig"
__version__ = pkg_resources.get_distribution("pinax-api").version


from . import authentication, permissions  # noqa
from .http import Response, Redirect  # noqa
from .mixins import DjangoModelEndpointSetMixin  # noqa
from .registry import register, bind, registry  # noqa
from .relationships import Relationship  # noqa
from .resource import Resource, Attribute  # noqa
from .tests.test import TestCase  # noqa
from .urls import URL as url  # noqa
from .views import handler404  # noqa
from .viewsets import ResourceEndpointSet, RelationshipEndpointSet  # noqa
