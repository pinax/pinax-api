## Examples

pinax-api usage examples, many taken from other portions of this documentation.

### Example: Automatically Obtain Object or 404

By default `api.EndpointSet.prepare()` does nothing. This means every endpoint must retrieve a specified resource themselves. However, by overriding `.prepare()` you can obtain a queryset and an object automatically.

```python
class AuthorEndpointSet(api.ResourceEndpointSet):

    def prepare(self):
        if self.requested_method in ["retrieve", "update", "destroy"]:
            self.pk = self.kwargs["pk"] if "pk" in self.kwargs else None
            self.obj = self.get_object_or_404(
                self.get_queryset(),
                pk=self.pk
            )
            
    def retrieve(self, request, pk):
        # No need to obtain correct queryset,
        # or find specified object in queryset,
        # or handle resulting errors!
        resource = self.resource_class(self.obj)
        return self.render(resource)
```

In this example `.update()` and `.destroy()` also benefit from automatic object retrieval.

### Example: Using `api.DjangoModelEndpointSetMixin`

If your resource obtains data from Django models you can inherit from `api.mixins.DjangoModelEndpointSetMixin` to get automatic queryset and object retrieval.

```python
class AuthorEndpointSet(api.DjangoModelEndpointSetMixin, api.ResourceEndpointSet):

    def retrieve(self, request, pk):
        resource = self.resource_class(self.obj)
        return self.render(resource)
```

In this example you don't need to override `.prepare()` because `DjangoModelEndpointSetMixin` handles that for you.

### Example: Restricting Access to All Endpoints

After authentication, `api.DjangoModelEndpointSetMixin.prepare()` obtains and saves the object PK and retrieves the object if it exists. pinax-api then checks permissions using your custom permission checker, `is_staff_or_self()`:

```python
# permissions.py

def is_staff_or_self(request, view):
    """
    Fail if non-staff user specifies object by any PK except "self".

    Requires view to provide a `pk` attribute.
    """
    if request.user.is_staff:
        return (True, 200, "")

    if view.pk != request.user.pk:
        return (False, 403, "ID must be \"{}\"".format(request.user.pk))
```

Add this permissions function to your EndpointSet:

```python
# endpoints.py

from .permissions import is_staff_or_self

class AuthorEndpointSet(api.DjangoModelEndpointSetMixin, api.ResourceEndpointSet):

    middleware = {
        "permissions": [
            is_staff_or_self,
        ]
    }

    def retrieve(self, request, pk):
        resource = self.resource_class(self.obj)
        return self.render(resource)
```

pinax-api automatically invokes `is_staff_or_self()` for all endpoints in AuthorEndpointSet. `is_staff_or_self()` references the saved `view.pk` attribute to determine if the requesting user can see the specified Author. In this case, staff may see any Author, while authors may only view their own Author resource.

### Example: Restricting Access to One Endpoint

Often you want to allow any user to view a collection of resources, but only allow staff to create, update, and delete resources. Since endpoint permission is granted by default, you must decorate these endpoint methods using `api.permission.add()`:

```python
from pinax import api

class UserEndpointSet(api.ResourceEndpointSet):

    @api.permission.add([app.permissions.is_staff])
    def create(self, request):
        ...
        
    def list(self, request):
        ...

    @api.permission.add([app.permissions.is_staff])
    def update(self, request, pk):
        ...

    @api.permission.add([app.permissions.is_staff])
    def retrieve(self, request, pk):
        ...
```

Note the permission function is enclosed in a list: `@api.permission.add([app.permissions.is_staff])`. Using a list allows processing multiple permission checks.

### Example: Allowing Anonymous Access to Endpoint

Sometimes you want anonymous users to be able to view a list of resources, but require authentication for all other resource endpoints. Since authentication is required by default, you must decorate the `list` method with `api.authentication.add()`:

```python
from pinax import api

class UserEndpointSet(api.ResourceEndpointSet):

    def create(self, request):
        ...
        
    @api.authentication.add([api.authentication.Anonymous()])
    def list(self, request):
        ...

    def update(self, request, pk):
        ...

    def retrieve(self, request, pk):
        ...
```

Note you instantiate the authenticator class and enclose it in a list: `@api.authentication.add([api.authentication.Anonymous()])`.

Instantiation provides an authentication class instance with callable `.authenticate()` method. Using a list allows processing multiple authentication backends.

### Example: Use `dict` as Resource Model

```python
@api.register
class PasswordResetResource(api.Resource):

    api_type = "passwordreset"
    model = dict
    attributes = [
        "email",
        api.Attribute("password", scope="w")
    ]

    def set_attr(self, attr, value):
        """Set dictionary attribute"""
        self.obj[attr.obj_attr] = value

    def get_attr(self, attr):
        """Get dictionary attribute"""
        return self.obj[attr.obj_attr]

    # Token handling methods not shown for clarity
    
    def set_token(self, token):
        self.obj["token"] = token

    @property
    def id(self):
        return self.obj["token"]
```

***
[Documentation Index](index.md)
