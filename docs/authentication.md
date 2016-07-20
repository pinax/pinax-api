## Authentication

`api.EndpointSet` authentication determines whether an endpoint requires authentication, and authenticates the user if necessary. Endpoints require authentication by default but may open access to anonymous users if needed.

`api.EndpointSet` checks authentication at three levels of granularity in the following order, from most specific to most general:

1. Endpoint authentication — This authentication applies to only the specified endpoint. Activated via endpoint `authentication` attribute.
2. Class authentication — This authentication applies to the entire EndpointSet class. Activated via class `middleware["authentication"]` attribute.
3. Django authentication — This authentication applies to the entire application. Straight from the pony's mouth using `self.request.user.is_authenticated` and the standard Django AUTHENTICATION_BACKENDS.

If authentication fails or succeeds at any level, more general authentication checks are not processed.

### Writing An Authenticator Class

`api.EndpointSet` authenticators are Python classes with an `.authenticate()` method. `.authenticate()` must accept a `Request` parameter and respond by either raising `AuthenticationFailed` or returning a user object (if authentication succeeded) or None (if authentication cannot be determined).

NOTE: Do not confuse Django authentication backends (referenced in settings.py AUTHENTICATION_BACKENDS) with pinax-api authentication backends. Django authentication backends allow overriding `get_user()`, while pinax-api authentication backends have no such method.

Here is a sample authenticator class, copied straight from pinax-api:

```python
class Anonymous(object):

    def authenticate(self, request):
        if not request.user.is_authenticated():
            from django.contrib.auth.models import AnonymousUser
            return AnonymousUser()
```

### EndpointSet Method Authentication

Authentication at the endpoint level is specified by an `authentication` attribute on the endpoint. Setting this attribute is accomplished by decorating the endpoint using `api.authentication.add()` with a list of pinax-api authentication classes. Method authentication only covers the decorated endpoint; all other endpoints use either their own authentication or one of the broader authentication methods (see below).

```python
from pinax import api
from .authentication import EAP  # Extensible Authentication Protocol class

class UserEndpointSet(api.ResourceEndpointSet):

    @api.authentication.add([EAP()])
    def create(self, request):
        ...
```

### EndpointSet Class Authentication

Authentication at the `api.EndpointSet` class level is specified by a `middleware` dictionary attribute on the class, with an `authentication` item containing a list of pinax-api authentication classes. EndpointSet class authentication covers all endpoints in the EndpointSet.

```python
from pinax import api

class UserEndpointSet(api.ResourceEndpointSet):

    middleware = {
        "authentication": [
            api.authentication.Anonymous(),
        ]
    }

    def create(self, request):
        ...
```

### Django Authentication

Provided by Django and using the standard AUTHENTICATION_BACKENDS setting.

If EndpointSet authentication methods pass through, pinax-api authenticates the user via Django authentication.

### Using Anonymous Authentication

pinax-api provides a simple [anonymous authenticator class](https://github.com/pinax/pinax-api/blob/master/pinax/api/authentication.py), `api.authentication.Anonymous`. This class returns `AnonymousUser` if request.user is not authenticated.

Note that pinax-api `Anonymous` authenticator class references `request.user.is_authenticated()`, which will invoke Django's authentication system if installed.

***
[Documentation Index](index.md)
