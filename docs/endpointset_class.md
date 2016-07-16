## EndpointSet

[Source code](https://github.com/pinax/pinax-api/blob/master/pinax/api/viewsets.py)

The `EndpointSet` class inherits from Django's `View` class. The EndpointSet class does not provide any URL resolution.

action implementations. In order to use a EndpointSet class you'll override the class and define the action implementations explicitly.

### Descendents

[`ResourceEndpointSet`](resourceendpointset_class.md)
[`RelationshipEndpointSet`](relationshipendpointset_class.md)

### Attributes

`requested_method`

`request`

`http_method_names = [u'get', u'post', u'put', u'patch', u'delete', u'head', u'options', u'trace']`

`http_method_not_allowed`

### Methods

Unless otherwise noted, all methods are defined by EndpointSet class.

#### `.as_view(cls, **initkwargs)`

#### `.check_authentication(self, endpoint)`

#### `.check_permissions(self, endpoint)`

#### `.create_top_level(self, resource, linkage=False, **kwargs)`

#### `.debug(self)`

#### `.dispatch(self, request, *args, **kwargs)`

#### `.error_response_kwargs(self, message, title=None, status=400, extra=None)`

#### `.get_object_or_404(self, qs, **kwargs)`

#### `.handle_exception(self, exc)`

#### `.parse_data(self)`

#### `.prepare(self)`

#### `.render(self, resource, **kwargs)`

#### `.render_create(self, resource, **kwargs)`

#### `.render_delete(self)`

#### `.render_error(self, *args, **kwargs)`

#### `.validate(self, resource_class, collection=False, obj=None)`

#### `.validate_resource(self, resource_class, resource_data, obj=None)`
