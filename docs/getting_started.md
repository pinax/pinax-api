## Getting Started

### Install `pinax-api`

Add "pinax-api" to your project `requirements.txt` file or install pinax-api manually:

```
$ pip install pinax-api
```

You need not add pinax-api to your INSTALLED_APPS because there are no pinax-api models. Instead just import pinax.api as needed.

### Use `pinax-api` In Your Application

Follow three steps to use pinax-api in your application. Let's imagine your Django application has an `Author` model with `name` and `birthdate` attributes, something like this:

```python
# models.py

from django.db import models

class Author(models.Model):
    name = models.CharField(max_length=50)
    birthdate = models.DateField()
```

#### 1. Create Your Resource


Expose the `Author` model `name` and `birthdate` attributes.

```python
# resources.py

from pinax import api
from .models import Author

@api.register
class AuthorResource(api.Resource):

    api_type = "author"
    model = Author
    attributes = [
        "name",
        "birthdate",
    ]

    @property
    def id(self):
        return self.obj.pk
```

#### 2. Create Your Resource Endpoints

This endpoint set allows listing all Author resources and retrieving a specific Author. Since our resource originates from a Django model, your EndpointSet class can inherit from `api.utils.DjangoModelEndpointSetMixin`.

```python
# endpoints.py

from pinax import api
from .resources import AuthorResource

@api.bind(resource=AuthorResource)
class AuthorEndpointSet(api.mixins.DjangoModelEndpointSetMixin, api.ResourceEndpointSet):
    """
    Author resource endpoints
    """
    url = api.url(
        base_name="author",
        base_regex=r"authors",
        lookup={
            "field": "pk",
            "regex": r"\d+"
        }
    )

    def list(self, request):
        """List all Authors"""
        return self.render(self.resource_class.from_queryset(self.get_queryset()))

    def retrieve(self, request, pk):
        """Retrieve an Author"""
        return self.render(self.resource_class(self.obj))
```

#### 3. Wire Up Your Resource Endpoints

pinax-api creates URL patterns for you automatically! For more details on automatic resource URL paths, see [URL Mapping](urlmapping.md).

```python
# urls.py

from django.conf.urls import url
from .endpoints import AuthorEndpointSet

urlpatterns = [
    # existing URL patterns
]

class API:
    name = "My Application API"
    endpointsets = [
        AuthorEndpointSet,
    ]

    def __iter__(self):
        return iter(self.endpointsets)

for endpointset in API.endpointsets:
    urlpatterns.extend(endpointset.as_urls())
```

## Need More Info?

Dive deeper and gain a better understanding of how pinax-api helps you out!

### Core Topics

* [Resources](resources.md)
* [Relationships](relationships.md)
* [EndpointSets](endpointset.md)

### Advanced Topics

* [Authentication](authentication.md)
* [Permissons](permissions.md)
* [API Documentation](api_documentation.md)


### References

* [URL Mapping](urlmapping.md)
* [Utilities](utilities.md)
* [Class Reference](classes.md)

### Examples & Tutorials

* [Examples](examples.md)
* [Tutorials](tutorials.md)

***
[Documentation Index](index.md)
