import pkg_resources


default_app_config = "pinax.api.apps.AppConfig"
__version__ = pkg_resources.get_distribution("pinax-api").version


from . import authentication, permissions  # noqa
from .http import Response  # noqa
from .registry import register, bind  # noqa
from .relationships import Relationship  # noqa
from .resource import Resource  # noqa
from .urls import URL as url, handler404  # noqa
from .viewsets import ResourceEndpointSet  # noqa
