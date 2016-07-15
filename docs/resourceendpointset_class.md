## ResourceEndpointSet

[Source code](https://github.com/pinax/pinax-api/blob/master/pinax/api/viewsets.py)

The `ResourceEndpointSet` class inherits from `EndpointSet` and provides default URL resolution for resource endpoints, but does not include any actions by default.

In order to use a `ResourceEndpoinSet` class you'll need to override the class and explicitly define the action endpoint implementations.

### Descendants

None

### Attributes

`requested_method`

`request`

`http_method_names = [u'get', u'post', u'put', u'patch', u'delete', u'head', u'options', u'trace']`

`http_method_not_allowed`

### Methods

#### `.view_mapping(cls, collection)`

#### `.as_urls(cls)`

### EndpointSet Methods

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

#### `render_error(self, *args, **kwargs)`

#### `.validate(self, resource_class, collection=False, obj=None)`

#### `.validate_resource(self, resource_class, resource_data, obj=None)`
