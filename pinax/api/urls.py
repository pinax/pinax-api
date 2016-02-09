from __future__ import unicode_literals

from django.core.urlresolvers import reverse


def as_absolute_url(resource_type, method, related_name=None, relationship=False, args=None, kwargs=None, request=None):
    name = [resource_type]
    if related_name is not None:
        name.append(related_name)
        if relationship:
            name.append("relationship")
    name.append(method)
    url = reverse("-".join(name), args=args, kwargs=kwargs)
    if request is not None:
        url = request.build_absolute_uri(url)
    return url
