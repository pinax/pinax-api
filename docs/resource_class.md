## Resource

[Source code](https://github.com/pinax/pinax-api/blob/master/pinax/api/resource.py)

### Descendants

None

### Attributes

`api_type = ""`
`attributes = []`
`relationships = {}`
`bound_viewset = None`

### Methods

#### `.view_mapping(cls, collection)`

#### `.from_queryset(cls, qs)`

#### `.populate(self, data, obj=None)`

#### `.create(self, **kwargs)`

#### `.update(self, **kwargs)`

#### `.save(self, create_kwargs=None, update_kwargs=None)`

#### `.identifier(self)`

#### `.resolve_url_kwargs(self)`

#### `.get_self_link(self, request=None)`

#### `.get_self_relationship_link(self, related_name, request=None)`

#### `.get_attr(self, attr)`

#### `.get_relationship(self, related_name, rel)`

#### `.get_relationship(self, related_name, rel)`

#### `.get_relationship(self, related_name, rel)`

#### `.get_relationship(self, related_name, rel)`

#### `.serializable(self, linkage=False, included=None, **kwargs)`
