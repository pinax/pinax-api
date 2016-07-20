## Resources

Resources are fundamental objects in pinax-api. Resources may represent Django models, either partially or fully. Resources may represent other objects, such as dicts. Resource classes define what data to show and what data to accept for CRUD operations on a Resource instance.

### Resource Definition

#### Required properties

Every `api.Resource` object MUST have three properties:

- `api_type` — string identifying the resource type. Must be unique among all Resources in a project.


- `model` —  object type, typically a Django class name, i.e. `Author`.


- `id` — any valid PK type, this is typically the PK of the underlying Django model instance

For instance:

```python
from pinax import api

class AuthorResource(api.Resource):
    api_type = "author"
    model = Author

    @property
    def id(self):
        return self.obj.pk

   ...
```

#### Optional Properties

Any `api.Resource` object MAY have one or more of the following properties:

- `attributes` — an [attributes object](http://jsonapi.org/format/#document-resource-object-attributes) representing some of the resource’s data.
- `relationships` — a [relationships object](http://jsonapi.org/format/#document-resource-object-relationships) describing relationships between the resource and other JSON API resources. See the [Relationships topic guide](relationships.md) for more details.

### Resource Attributes

Resource `.attributes` define the resource data to expose for retrieval and accepted for update. Attributes may refer to Django model fields or resource properties.

All resource attributes define single-object attributes. Integer fields, char fields, and boolean fields are examples of singleton attributes.

Although ForeignKey relationships are single-object, the JSON:API spec [explicitly states](http://jsonapi.org/format/#document-resource-object-attributes)

> Although has-one foreign keys (e.g. author_id) are often stored internally alongside other information to be represented in a resource object, these keys SHOULD NOT appear as attributes.

ForeignKey, OneToMany, and ManyToMany fields are represented as relationships defined in `api.Resource.relationships`. See the [Relationships topic guide](relationships.md) for more details.


#### Model Field Attributes

Given a simple `Author` Django model:

```python
# models.py

from django.db import models

class Author(models.Model):
    name = models.CharField(max_length=50)
    birthdate = models.DateField()

    def __str__(self):
        return self.name
```

you might define an `AuthorResource` by referencing the `Author.name` attribute:

```python
from pinax import api

class AuthorResource(api.Resource):
    api_type = "author"
    model = Author
    attributes = [
        "name",
    ]
    ...
```

This `AuthorResource` exposes `Author.name` for retrieval or update. `Author.birthdate` is not visible.

#### Resource Property Attributes

Resource attributes expose resource properties. A resource property might be a calculated value. For instance, the `AuthorResource` class might include a property which returns the authors age:

```python
import datetime
from pinax import api

class AuthorResource(api.Resource):
    api_type = "author"
    model = Author
    attributes = [
        "name",
        "age",  # poor resource design, allows both read and write
    ]

    @property
    def age(self):
        return datetime.date.today() // self.obj.birthdate

    ...
```

In this example `AuthorResource` exposes `Author.age` for both retrieval and update. One cannot change an authors age, so that attribute should be read-only. This gives us an excuse to introduce `api.Attribute`:

```python
import datetime
from pinax import api

class AuthorResource(api.Resource):
    api_type = "author"
    model = Author
    attributes = [
        "name",
        api.Attribute("age", scope="r"),  # only read, no write
    ]

    @property
    def age(self):
        return datetime.date.today() // self.obj.birthdate

    ...
```

#### Enhanced Attributes with `api.Attribute`

The `api.Attribute` class performs two functions. First, it allows a resource attribute to be either read-only, write-only, or both. By default all attributes are read/write. Second, it permits decoupling the resource attribute name from the underlying object field name.

##### Read-Only Attribute

An authors age should be read-only:

```python
class AuthorResource(api.Resource):
    api_type = "author"
    model = Author
    attributes = [
        "name",
        api.Attribute("age", scope="r"),  # only read, no write
    ]
```

##### Write-Only Attribute

Do not reveal an account password, make it write only:

```python
class AccountResource(api.Resource):

    api_type = "account"
    attributes = [
        "email",
        api.Attribute("password", scope="w"),  # only write, no read
    ]
```

##### Decoupling Resource from Model

With a model like this:

```python
class Author(models.Model):
    name = models.CharField(max_length=50)
    birthdate = models.DateField()
    extra = models.CharField(max_length=100)  # general notes

    def __str__(self):
        return self.name
```

A resource may want a different attribute name for external consumption. In this case the resource exposes `notes`, derived from `Author.extra`:

```python
class AuthorResource(api.Resource):

    api_type = "author"
    attributes = [
        "name",
        api.Attribute("notes", obj_attr="extra"),
    ]
```

#### Combining Attributes

Consider two Resources, `BillingAddressResource` and `ShippingAddressResource`. Both inherit from a third resource, `AddressResource`, which is abstract and has no endpoints.

```python
class AddressResource(api.Resource):

    attributes = [
        "address1",
        "address2",
        "city",
        "state",
        "zipcode",
        "country",
    ]

    @property
    def id(self):
        return self.obj.pk


@api.register
class BillingAddressResource(AddressResource):

    api_type = "billingaddress"
    model = BillingAddress


@api.register
class ShippingAddressResource(AddressResource):

    api_type = "shippingaddress"
    model = ShippingAddress
    attributes = set(chain.from_iterable([
        AddressResource.attributes,
        [
            "attn",
        ],
    ]))
```

First, note `AddressResource` has no `api_type` attribute and no `model` attribute because it is an abstract class. However, both `BillingAddressResource` and `ShippingAddressResource` inherit from `AddressResource` and must provide `api_type` and `model`.  Each inheriting class defines their own `api_type` and `model`, adding attributes as needed. In our example, `BillingAddressResource` doesn't need any additional fields, but `ShippingAddressResource` includes an `attn` field, presumably present on the `ShippingAddress` Django model.

### Other Resource Properties

* `obj` — a resource's underlying object instance

An `api.Resource` instance always contains a pointer to the underlying object instance in `self.obj`. In the examples above, resource properties reference `self.obj.pk` and `self.obj.birthdate`. These references to `self.obj` act on the `Author` instance attached to the resource instance.

***
[Documentation Index](index.md)
