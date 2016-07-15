## EndpointSets

`api.EndpointSet`-based classes provide a framework for manipulating and retrieving resources. `api.EndpointSet` uses specific URL paths and HTTP requests based on the JSON:API [specification](http://jsonapi.org/format/). `api.EndpointSet` inherits from Django's generic class-based views, specifically `django.views.generic.base.View`, so all `View` methods and attributes are available.

pinax-api provides two types of EndpointSet classes: `api.ResourceEndpointSet` and `api.RelationshipEndpointSet`. We will discuss ResourceEndpointSets first because relationships cannot exist without resources.

### Serving Resources

Serving resources requires four steps:

1. Create a class inheriting from `api.ResourceEndpointSet`
2. Provide URL path naming and object identifier conventions
3. Bind a Resource to the new ResourceEndpointSet-based class
4. Add specially-named methods for each supported resource action.

#### Step One: Inherit from api.ResourceEndpointSet

To manipulate and retrieve Resources, create a class which inherits from `api.ResourceEndpointSet`.

```python
from pinax import api

class AuthorEndpointSet(api.ResourceEndpointSet):
    ...
```

#### Step Two: Specify URL name and Object Identifier

Every ResourceEndpointSet must have a `url` attribute. This attribute defines the base URL pathname for the endpoint, along with specifics for keyed resource retrieval.

```python
from pinax import api

class AuthorEndpointSet(api.ResourceEndpointSet):

    url = api.url(
        base_name="author",
        base_regex=r"authors",
        lookup={
            "field": "pk",
            "regex": r"\d+"
        }
    )
```

Endpoints reference Author resources by a "pk" attribute, specified in `url.lookup["field"]`. The PK in this case is an integer primary key, specified by the `url.lookup["regex"]` regular expression.

This example results in two automatic URL paths for accessing endpoints:

```python
authors
authors/<pk>
```

#### Step Three: Bind ResourceEndpointSet To Resource Class

Most JSON:API endpoints return an HttpResponse containing some form of JSON-serialized resource data. The JSON:API [specification](http://jsonapi.org/format/#document-resource-objects) states resource response payloads MAY include links to their own endpoint in this response:

> In addition, a resource object **MAY** contain any of these top-level members:
>
> - `links`: a [links object](http://jsonapi.org/format/#document-links) containing links related to the resource.

and pinax-api always includes these links. However, `api.Resource` classes by themselves don't know anything about endpoints and URL paths. In order to provide this "self" URL link resolution, you must connect the Resource class with the ResourceEndpointSet class using `api.bind()`.

**Bind Resource classes to EndpointSets to provide URL resolution for resource rendering.**

pinax-api uses a "bound" ResourceEndpointSet to determine the URL patterns for a resource `self` link. Unbound resource classes do not contain any URL patterns and therefore cannot be rendered.

Binding a ResourceEndpointSet with a Resource class has three results:

1. creates a new "bound" resource class which associates the original Resource class with the ResourceEndpointSet class
2. adds a `resource_class` attribute to the ResourceEndpointSet, pointing to the new "bound" resource class
3. registers the new "bound" resource class in the api registry

Bind a Resource class to a ResourceEndpointSet by decorating with `api.bind()`:

```python
from pinax import api
from .resources import UserResource

@api.bind(resource=UserResource)
class UserEndpointSet(api.ResourceEndpointSet):
    ...
```

#### Step Four: Create Resource Endpoints

Resource retrieval and manipulation is performed by ResourceEndpointSet methods, called "endpoints". These methods have specific names based on automatic HTTP method to URL mapping. See [URL Mapping](urlmapping.md) for more details.

Your EndpointSet does not need to implement all possible endpoints, just the endpoints you wish to support. The following list shows examples of each type of endpoint.

##### Possible Resource Endpoints

###### SHOW RESOURCE

* `.list()` - show collection of resources

  Use `.resource_class.from_queryset()` to render a collection of resources:

  ```python
      def list(self, request):
          return self.render(
              self.resource_class.from_queryset(self.get_queryset())
          )
  ```

  The JSON:API [specification](http://jsonapi.org/format/#fetching-filtering) permits filtering data using a `filter` query parameter:

  > The `filter` query parameter is reserved for filtering data. Servers and clients **SHOULD** use this key for filtering operations.

  How you implement filtering is up to you:

  ```python
      def list(self, request):
          queryset = self.get_queryset()
          filter = request.GET.get("filter", "")
          if filter:
              queryset = filter_queryset(queryset, filter)  # your filtering func
          return self.render(self.resource_class.from_queryset(queryset))

  ```


* `.retrieve()` - show single resource

  Show a retrieved object:

  ```python
      def retrieve(self, request, pk):
          resource = self.resource_class(self.obj)
          return self.render(resource)
  ```

###### CREATE / MODIFY RESOURCE

* `.create()` - create new resource

  Requires validation of user-provided data, automatically handled by `.validate()`. Use `.render_create()` for rendering a new resource:

  ```python
      def create(self, request):
          with self.validate(self.resource_class) as resource:
              resource.save()
          return self.render_create(resource)
  ```


* `.update()` - update resource

  Requires validation of user-provided data, automatically handled by `.validate()`:

  ```python
      def update(self, request, pk):
          with self.validate(self.resource_class, obj=self.obj) as resource:
              resource.save()
          return self.render(resource)
  ```

  This validation combines the existing object (`self.obj`) with user-provided data and the resource class for validation.

###### DESTROY RESOURCE

* `.destroy()` - delete resource

  Delete a retrieved object:

  ```python
      def destroy(self, request, pk):
          self.obj.delete()
          return self.render_delete()
  ```

##### Validating Resource Data

pinax-api validates user-provided resource data via `EndpointSet.validate()`. This method ensures:

* POST data is parseable into JSON

* POST data contains a `data` element, as per JSON:API [specification](http://jsonapi.org/format/#document-top-level):

  > A document **MUST** contain at least one of the following top-level members:
  >
  > - `data`: the document’s “primary data”
  > - `errors`: an array of [error objects](http://jsonapi.org/format/#errors)
  > - `meta`: a [meta object](http://jsonapi.org/format/#document-meta) that contains non-standard meta-information.

* POST data is a list for resource collections

* POST `data` element contains an `attributes` element

Furthermore, `.validate()` discards POST data which is not part of the resource attributes. For example, given a resource definition:

```python
from pinax import api

class AuthorResource(api.Resource):
    api_type = "author"
    model = Author
    attributes = [
        "name",
    ]
```

 if the POST data contained:

```python
    "data": {
        "attributes": {
            "name": "Robert Heinlein",
            "email": "rheinlein@scifi.com",
            "phone": "970-555-1212"
        }
    }
```

validation would ignore the "email" and "phone" fields and only update the "name" attribute.

###### ContextManager

Note that `EndpointSet.validate()` is a context manager, so you will always invoke it in the context of a `with` statement. `.validate()` returns either a resource or a resource iterator:

```python
# validate single resource
with self.validate(self.resource_class) as resource:
    # do something with the resource
    ...

# validate resource collection
with self.validate(self.resource_class, collection=True) as resources:
    for resource in resources:
        # do something with each resource
        ...
```

##### Rendering Resources

Resource rendering produces a JSON:API-compliant representation of resources, suitable for use by API consumers. Rendering is required for `.list()`, `.create()`, `.update()`, and `.retrieve()` endpoints, as per the JSON:API [specification](http://jsonapi.org/format/#crud-creating-responses-201):

> The response **MUST** also include a document that contains the primary resource...

Rendering is usually the last task an endpoint performs. pinax-api provides three rendering methods for "success" responses:

* `.render()` - return an HttpResponse with rendered resource instance (or collection of instances) based on existing, newly created, or updated data
* `.render_create()` - return an HttpResponse with JSON:API-compliant payload for a newly created resource
* `.render_delete()` - return an HttpResponse with no payload and 204 status_code

Standard endpoints instantiate a resource instance using `.resource_class()`, never by referencing the resource class directly. `.resource_class()` takes advantage of Resource - ResourceEndpointSet binding (see "Step Three: Bind ResourceEndpointSet To Resource Class" above) to determine the resource class.

- `.resource_class()` - return the bound `api.Resource`-based resource class

This is correct:

```python
from pinax import api
from .resources import UserResource

@api.bind(resource=UserResource)
class UserEndpointSet(api.ResourceEndpointSet):

    def retrieve(self, request, pk):
        ...
        resource = self.resource_class(obj)  # creates "bound" resource
        return self.render(resource)
```

If a resource is INCORRECTLY instantiated directly from the resource class:

```python
from pinax import api
from .resources import UserResource

@api.bind(resource=UserResource)
class UserEndpointSet(api.ResourceEndpointSet):

    def retrieve(self, request, pk):
        ...
        resource = UserResource(obj)  # creates unbound resource
        return self.render(resource)
```

pinax-api will complain during `self.render()`:

```python
"AssertionError: resolve_url_kwargs requires a bound resource (got <myapp.resources.UserResource object at 0x10cf77d30>)."
```

Resource rendering fails in this case because the Resource instance is not associated with an ResourceEndpointSet and therefore the resource "self" link required by JSON:API cannot be generated. Remember: **always render "bound" resources**.

##### Returning Errors

When your endpoint detects a problem, invoke `.render_error()`. If a `status` kwarg is not provided, `.render_error()` sets the response status_code to 400.

- `.render_error(status=400)` - return an HttpResponse with error message and status code

```python
from pinax import api
from .resources import PasswordResetResource

@api.bind(resource=PasswordResetResource)
class PasswordResetEndpointSet(api.ResourceEndpointSet):

    def retrieve(self, request, token):
        email = self.validate_token(token)
        if email is not None:
            # Do some stuff
            return(payload)
        else:
            return self.render_error("Invalid or expired password reset token")

```
#### Using Django Models in Resources

If your resource serves data from Django models you can inherit from `api.mixins.DjangoModelEndpointSetMixin` to get automatic queryset and object retrieval. For instance, instead of:

```python
from pinax import api

class AuthorEndpointSet(api.ResourceEndpointSet):
    ...

    def list(self, request):
        """List all Authors"""
        qs = Author.objects.all()
        return self.render(self.resource_class.from_queryset(qs))

    def retrieve(self, request, pk):
        """Retrieve an Author"""
        qs = Author.objects.all()
        author = self.get_object_or_404(qs, pk)
        return self.render(self.resource_class(author))
```

you can write:

```python
from pinax import api

class AuthorEndpointSet(api.mixins.DjangoModelEndpointSetMixin, api.ResourceEndpointSet):
    ...

    def list(self, request):
        """List all Authors"""
        return self.render(self.resource_class.from_queryset(self.get_queryset()))

    def retrieve(self, request, pk):
        """Retrieve an Author"""
        return self.render(self.resource_class(self.obj))
```

`DjangoModelEndpointSetMixin` provides three new methods and overrides a fourth:

* `.get_pk()` - return the PK value for the Django model object
* `.get_resource_object_model()` - return the resource class underlying model
* `.get_queryset()` - return QuerySet of all resource class underlying model instances
* `.prepare()` - sets `self.pk` and `self.obj` if HTTP request method acts on single objects. Raises 404 if object is not found in queryset using specified PK.

##### Resource Proxying

An endpoint might need to render a different resource class because the endpoint is proxying for several resource types. In this case you cannot use `.resource_class()` since it's the wrong resource, and  you should not reference the desired resource class directly (as seen above).
Instead obtain the *bound* resource class from the api registry:

```python
from pinax import api

@api.bind(resource=UserResource)
class UserEndpointSet(api.ResourceEndpointSet):

    def retrieve(self, request, pk):
        ...
        if user is special:
            resource_class = api.registry["specialuser"]
        else:
            resource_class = api.registry["otheruser"]
        return self.render(resource_class(obj))
```

Remember: If you cannot use `.resource_class()` to obtain a resource class, **get a bound resource from the API registry**.

### More Reading

Check out [Relationships](relationships.md) for details about resource relationships.

***
[Documentation Index](index.md)

