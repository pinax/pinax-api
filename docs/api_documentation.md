## Automatic API Documentation

pinax-api can produce API documentation if you follow two steps:

### 1. Format API Endpoint Docstring

API documentation can be automatically created from EndpointSet method docstrings. Endpoint docstrings must follow the  API Blueprint [specification](https://apiblueprint.org/) in order to provide automatic documentation details. Note that docstring indentation is critical. Here is an example documenting the Author `.retrieve()` endpoint:

```python
class AuthorEndpointSet(DjangoModelEndpointSetMixin, api.ResourceEndpointSet):
    ...

    def retrieve(self, request, pk):
        """
        Identifier: Retrieve an author

        + Parameters

            + id: `1` (required, int) - The author ID.

        + Response 200 (application/vnd.api+json)

            Retrieved Author

            + Body

                    {
                        "jsonapi": {"version": "1.0"},
                        "data": {
                            "type": "author",
                            "id": "55",
                            "attributes": {
                                "name": "Robert Heinlein",
                                "age": 109
                            },
                            "links": {
                                "self": "https://<api>/authors/55"
                            },
                            "relationships": {
                                "groups": {
                                    "data": []
                                }
                            }
                        },
                        "links": {
                            "self": "https://<api>/authors/55"
                        }
                    }


        + Response 404 (application/vnd.api+json)

                    {
                        "jsonapi": {"version": "1.0"},
                        "errors": [
                            {
                                "detail": "Author not found",
                                "status": "404"
                            }
                        ]
                    }

        + Response 401 (application/vnd.api+json)

                    {
                        "jsonapi": {"version": "1.0"},
                        "errors": [
                            {
                                "detail": "Authentication is required.",
                                "status": "401"
                            }
                        ]
                    }
        """
        return self.render(self.resource_class(self.obj))
```

### 2. Wire Up API Documentation

pinax-api creates URL patterns for you automatically via the `doc_view()` utility. Serve automatic documentation at `/docs` by following this example:

```python
# urls.py

from django.conf.urls import url
from pinax.api.docs import doc_view
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

urlpatterns.append(url(r"^docs$", doc_view(API), name="docs"))
```

***
[Documentation Index](index.md)
