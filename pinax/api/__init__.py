import pkg_resources


default_app_config = "pinax.api.apps.AppConfig"
__version__ = pkg_resources.get_distribution("pinax-api").version


from .http import Response  # noqa
from .relationships import Relationship  # noqa
from .viewsets import (  # noqa
    ViewSet,
    ResourceViewSet,
    ResourceURL,
)
