## Relationships

Relationships are associations between resources. Authors have relationships with Posts, Users have relationships with Groups, and dogs have relationships with their masters :-).

When using pinax-api you define relationships in two places: in a Resource and in a ResourceEndpointSet.

### Resource Relationships

#### Why Use Relationships?

You define resource relationships in order to expose related data when rendering a resource. If you define a relationship between an Author and her Agent, a rendered Author object contains a URL link for the related Agent.

#### Defining Relationships

The resource class `relationships` attribute defines relationships. These relationships reference other resources rather than attributes of the primary resource. For instance:

```python
from pinax import api

@api.register
class AuthorResource(api.Resource):
    api_type = "account"
    attributes = [
        "name",
    ]
    relationships = {
        "tags": api.Relationship("authortag", collection=True),
        "agent": api.Relationship("agent")
    }
```

This resource relates an Author to a collection of "authortag" resources, as well as a single "agent" resource. At the model level, this relationship might look like this:

```python
class Author(models.Model):
    name = models.CharField(max_length=100)
    agent = models.ForeignKey(Agent, null=True)
    
class AuthorTag(models.Model):
    label = models.CharField(max_length=50)
    author = models.ForeignKey(Author)
```

**CAUTION**: Although technically the Author model defines the `Author.agent` relationship, the JSON:API [specification](http://jsonapi.org/format/#document-resource-object-attributes) indicates this type of relationship SHOULD NOT appear as an attribute:

> Although has-one foreign keys (e.g. `author_id`) are often stored internally alongside other information to be represented in a resource object, these keys **SHOULD NOT** appear as attributes.

DO NOT create a resource with a related-object attribute like this:

```python
from pinax import api

@api.register
class AuthorResource(api.Resource):
    api_type = "account"
    attributes = [
        "name",
        "agent",  # INCORRECT, related objects cannot be attributes
    ]
    relationships = {
        "tags": api.Relationship("authortag", collection=True),
    }
```

#### Related Resource Collections

If an object relationship is a collection, the object's `related_name` must produce either a Django QuerySet or an iterable. For instance `Product.images` below produces an iterable of related `ProductImages`:

```python
class ProductImage(models.Model):
    product = models.ForeignKey(Product)
    image = models.CharField(max_length=200, blank=True)
    content_type = models.CharField(max_length=200)

class Product(models.Model):
    category = models.ForeignKey(Category)
    name = models.CharField(max_length=200)
    slug = models.CharField(max_length=200)

    @property
    def images(self):
        yield ProductImage.default()
        for image in self.productimage_set.all():
            yield image
```

If the resource relation `related_name` does not produce a QuerySet or iterable, pinax-api will complain.

### ResourceEndpointSet Relationships

In order to provide related resource linkage, ResourceEndpointSets must specify RelationshipEndpointSet relationships. Unsurprisingly, ResourceEndpointSets define relationships by a `relationships` attribute. For example:

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
    relationships = {
        "agent": AuthorAgentEndpointSet,
        "tags": AuthorTagCollectionEndpointSet
    }
```

If a Resource HAS defined relationships and a ResourceEndpointSet DOES NOT, URL linkage for the related resource will not be generated. This does not violate the JSON:API [specification](http://jsonapi.org/format/#document-resource-objects) which states "relationships" are optional:

>In addition, a resource object **MAY** contain any of these top-level members:
>
>- `relationships`: a [relationships object](http://jsonapi.org/format/#document-resource-object-relationships) describing relationships between the resource and other JSON API resources.

### RelationshipEndpointSets

RelationshipEndpointSets are similar to ResourceEndpointSets. They use the same authentication and permission systems, and have similar automatically mapped endpoints. However, RelationshipEndpointSets should not create or update resources but instead add and remove relationship members.

#### Serving Relationships

Serving resource relationships requires two steps:

1. Create a class inheriting from `api.RelationshipEndpointSet`
2. Add specially-named methods (endpoints) for each supported resource action.

##### Step One: Inherit from api.RelationshipEndpointSet

To manipulate and retrieve Resource relationships, inherit from `api.RelationshipEndpointSet`.

```python
from pinax import api

class AuthorTagCollectionEndpointSet(api.RelationshipEndpointSet):
    ...
```

##### Step Two: Create Relationship Endpoints

Resource relationship retrieval and manipulation is performed by RelationshipEndpointSet methods, called "endpoints". These methods have specific names based on automatic HTTP method to URL mapping. See [URL Mapping](urlmapping.md) for more details.

#### Supported Endpoints

- `.retrieve()` - retrieve relationship members
- `.create()` - add members to relationship (**does not** imply related-object creation)
- `.update()` - replace relationship members (**does not** imply related-object update)
- `.destroy()` - delete relationship members

None of these methods should create or update resources, they should just change the relationship members for the resource. According to JSON:API [specification](http://jsonapi.org/format/#crud-updating-relationships) the only exception to this policy is `.destroy()`:

> Note: A server may choose to delete the underlying resource if a relationship is deleted (as a garbage collection measure).

#### Empty RelationshipEndpointSets

You may choose not to implement relationship endpoints even when relationships exist. *In this case you should still define the RelationshipEndpointSet class.*

If a relationship is correctly defined in the Resource and in the ResourceEndpointSet, the retrieved resource will contain URL links to the related resource. However, related resource requests will fail because no relationship endpoints exist.

In our AuthorEndpointSet above, "tags" refers to `AuthorTagCollectionEndpointSet`. If you don't want relationship endpoints, simply define an empty RelationshipEndpointSet class:

```python
from pinax import api

class AuthorTagCollectionEndpointSet(api.RelationshipEndpointSet):
    pass
```

### Relationship Authentication and Permissions

pinax-api supports several levels of EndpointSet authentication and permission checking. See [Authentication](authentication.md) and [Permissions](permissions.md) for more details.

***

[Documentation Index](index.md)
