## Permissions

`api.EndpointSet` permissions determine if the user may perform the endpoint action. Permission is granted by default, but pinax-api allows finer access control.

pinax-api checks permissions at two levels of granularity, in the following order:

1. Endpoint permissions — These permissions checks apply to only the specified endpoint. Activated via endpoint `permissions` attribute.
2. Class permissions — These permissions checks apply to the entire EndpointSet-based class. Activated via class `middleware["permissions"]` attribute.

If permissions checking fails or succeeds at any level, more general permission checking is not processed.

### Writing A Permissions Checker

EndpointSet permission checkers are Python functions. Permission functions must accept two required parameters, a Request object and the instantiated EndpointSet-based class. A permission function should return either nothing (unable to determine permissions) or a tuple `(ok, status, msg)` indicating whether the user has appropriate permissions.

```
def my_perm_checker(request, endpointset):
    ...
    return ok, status, msg
```

* ok — "user has permission", either True or False
* status — HTTP status code integer, only used if permissions check fails
* msg — error message string, only used if permissions check fails

Here is a simple permissions check function:

```python
def is_staff(request, endpointset):
    """
    Determine if request.user is "staff".
    """
    if request.user.is_staff:
        return (True, 200, "")
    return (False, 403, "User is not staff")
```

### EndpointSet Method Permissions

Permission checking at the endpoint level is specified by a `permissions` attribute on the endpoint. Setting this attribute is accomplished by decorating the endpoint using `api.permissions.add()` with a list of permission functions. This permission checking only covers the decorated endpoint; all other endpoints use either their own permission checking or one of the broader permission checking methods (see below). In this example, `is_staff()` permission checking is only needed for the `create` endpoint.

```python
from pinax import api

class UserEndpointSet(api.ResourceEndpointSet):

    @api.permission.add([app.permissions.is_staff])
    def create(self, request):
        ...
```

### EndpointSet Class Permissions

Permission checking at the EndpointSet class level is specified by a `middleware` dictionary attribute on the class, with a `permissions` item containing a list of permission functions. This permission checking covers all EndpointSet endpoints. In this example, `is_staff()` permission checking is required for all UserEndpointSet endpoints.

```python
from pinax import api

class UserEndpointSet(api.ResourceEndpointSet):

    middleware = {
        "permissions": [
            app.permissions.is_staff,
        ]
    }

    def create(self, request):
        ...
```

***
[Documentation Index](index.md)
