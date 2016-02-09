import pkg_resources


default_app_config = "pinax.api.apps.AppConfig"
__version__ = pkg_resources.get_distribution("pinax-api").version
