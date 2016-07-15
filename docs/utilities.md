## Utilities

### from pinax.api import docs

#### `.doc_view(api)`

A simple Django view which returns API documentation in "text/vnd.apiblueprint" format, assembled from EndpointSet docstrings.

To add an API documentation endpoint, define a class with all API endpointsets, then add `doc_view(cls)` to urlpatterns:

```python
# urls.py

from pinax.api import docs
from .endpoints import AuthorEndpointSet, GroupEndpointSet, AddressEndpointSet

class API:

    endpointsets = [
        AuthorEndpointSet,
        GroupEndpointSet,
        AddressEndpointSet,
    ]

    def __iter__(self):
        return iter(self.endpointsets)

urlpatterns.append(url(r"^docs$", docs.doc_view(API), name="docs"))
```

### from pinax.api import rfc3339

[RFC3339](https://tools.ietf.org/html/rfc3339) defines a date and time format for use in Internet protocols. You can convert to and from this format using the pinax-api rfc3339 utility functions:

#### `.parse(text)`

Accepts a timestamp string in RFC3339 format and returns a datetime.datetime object.

```python
>>> from pinax.api.rfc3339 import parse
>>> date = '2016-07-13T14:37:00.0Z'
>>> parse(date)
datetime.datetime(2016, 7, 13, 14, 37, tzinfo=<pinax.api.rfc3339.parse.<locals>.ZuluTZ object at 0x10f2fe0f0>)
```

#### `.encode(date)`

Accepts a datetime.datetime object and returns a string representation using the RFC3339 standard. This is handy for testing JSON response payloads. For instance, if your expected test payload includes a timestamp string for the Author creation date, you can encode the `Author.created` datetime.datetime object thusly for testing:

```python
from pinax import api

class Tests(api.TestCase):

    def test_get_author(self):
        expected = {
            ...
                "attributes": {
                    "created": rfc3339.encode(author.created),
                    "name": author.name,
                },
            ...
        }
        response = self.client.get(...)
        payload = json.loads(response.content.decode("utf-8"))
        self.assertEqual(expected, response)
```

pinax-api uses `rfc3339.encode()` when encoding datetime objects during rendering.

### from pinax import api

#### `.handler404(request)`

A simple Django 404 handler with error response formatted for the JSON:API [specification](http://jsonapi.org/format/#fetching-resources-responses-404).

To use this handler assign it to `handler404` in the project root URLconf:

```python
# urls.py

from pinax import api

handler404 = "api.handler404"
...
```

***
[Documentation Index](index.md)
