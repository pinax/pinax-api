## Automatic URL Mapping

EndpointSets provide **automatic** mapping from HTTP request type to EndpointSet endpoint methods. This mapping requires endpoints with specific names.

### Resource Mapping

Given an Author Resource:

```python
from pinax import api

class AuthorResource(api.Resource):
    api_type = "author"
    model = Author
    attributes = [
        "name",
    ]
```

and an Author EndpointSet:

```python
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

`api.ResourceEndpointSet` provides this mapping:

| Action              | HTTP method | Example path | Endpoint name |
| :------------------ | :---------: | :----------- | :------------ |
| list resources      |    `GET`    | `authors`    | `.list()`     |
| create new resource |   `POST`    | `authors`    | `.create()`   |
| retrieve resource   |    `GET`    | `authors/5`  | `.retrieve()` |
| update resource     |   `PATCH`   | `authors/5`  | `.update()`   |
| delete resource     |  `DELETE`   | `authors/5`  | `.destroy()`  |

See also JSON:API [Fetching Resources](http://jsonapi.org/format/#fetching-resources) and JSON:API [Creating, Updating, and Deleting Resources](http://jsonapi.org/format/#crud).

### Relationship Mapping

Given an Author Resource associated with Group Resources:

```python
from pinax import api

class AuthorResource(api.Resource):
    api_type = "author"
    model = Author
    attributes = [
        "name",
    ]
    relationships = {
        "groups": api.Relationship("group", collection=True),
    }

```

and an Author EndpointSet which exposes the relationship:

```python
class AuthorEndpointSet(api.ResourceEndpointSet):

    url = api.url(
        base_name="author",
        base_regex=r"authors",
        lookup={
            "field": "pk",
            "regex": r"\d+"
        }
    )
    relationships = {
        "groups": AuthorGroupCollectionEndpointSet,
    }
```


`api.RelationshipEndpointSet` provides this mapping:

| Action                        | HTTP method | Example path                     | Endpoint name |
| :---------------------------- | :---------: | :------------------------------- | :------------ |
| retrieve relationship members |    `GET`    | `authors/5/relationships/groups` | `.retrieve()` |
| add members to relationship   |   `POST`    | `authors/5/relationships/groups` | `.create()`   |
| replace relationship members  |   `PATCH`   | `authors/5/relationships/groups` | `.update()`   |
| delete relationship members   |  `DELETE`   | `authors/5/relationships/groups` | `.destroy()`  |

See also JSON:API [Fetching Relationships](http://jsonapi.org/format/#fetching-relationships) and JSON:API [Updating Relationships](http://jsonapi.org/format/#crud-updating-relationships).

***
[Documentation Index](index.md)
