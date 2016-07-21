
## pinax-api Overview

pinax-api helps developers provide a [JSON:API](http://jsonapi.org/)-compliant API for their Django applications. The pinax-api framework assists with defining API resources and their manipulation via HTTP endpoints.

### Architecture

#### Resources

pinax-api revolves around managing resources. Resources inherit from `api.Resource` and represent data to the outside world. Resources can be full or partial representations of Django models. Alternatively, you may build resources from dictionaries or some other object type. See the [Resources topic guide](resources.md) for more details.

#### Relationships

Relationships connect resources to other resources. Relationships are similar to Django's `ForeignKey`, `ManyToManyField`, and `OneToManyField` model fields. pinax-api relationships connect related resources using the `api.Relationship` class, specifying whether the related object is a singleton (`ForeignKey`) or a collection of resources (`ManyToManyField` and `OneToManyField`). See the [Relationships topic guide](relationships.md) for more details.

#### Endpoints

Applications serve resources and relationships from methods (referred to as “endpoints”) in an `api.EndpointSet`-based class. Each endpoint handles either creating, updating, retrieving, or deleting resources.

pinax-api provides two `EndpointSet`-based classes: `ResourceEndpointSet` and `RelationshipEndpointSet`. A ResourceEndpointSet manipulates resources, while a RelationshipEndpointSet manipulates resources related to another resource. See the [Endpoints topic guide](endpointset.md) for more details.

### Authentication and Permissions

pinax-api manages authentication and permissions for `api.EndpointSet`-based classes.

When processing an HTTP request, pinax-api performs authentication and permissions checks in the following order:

1. Authenticate User — is user authenticated?
2. Prepare Data — obtain resource data, available for permissions check
3. Check Permissions — does user have permission to access/manipulate this resource?
4. Invoke Endpoint

If authentication, preparation, or permissions checks encounter an error, they raise an exception and the endpoint is not invoked.

#### Authentication

Authentication is required for all endpoints by default, but allowing anonymous users is easy. See the [Authentication topic guide](authentication.md) and [Examples](examples.md) for more details.

#### Prepare

EndpointSet classes provide a hook method named `prepare()`, called after authentication and before permission checking. This method allows common operations in an EndpointSet. For example, after authentication `prepare()` might obtain a queryset or object for later manipulation. See the [Tutorials guide](tutorials.md) for examples of overriding `prepare()`.

#### Permissions

Endpoint permission is granted by default, but adding restrictions is easy. See the [Permissions topic guide](permissions.md) and [Examples](examples.md) for more details.

### Automatic API Documentation

API documentation helps developers understand how to interact with your application. pinax-api can provide automatic documentation based on docstrings in your ResourceEndpointSets and RelationshipEndpointSets.

See the [Automatic API Documentation topic guide](api_documentation.md) for more details.

## Documentation Notes

Code examples throughout this documentation do not always follow PEP8 and Django standards. Specifically we remove extra blank lines normally separating import groups and prior to class definitions in order to compress the example code for readability. In real-world development we heartily recommend following PEP8 and Django standards.

***
[Documentation Index](index.md)
