from __future__ import unicode_literals

from pinax.api import ResourceURL, ResourceViewSet


class UserViewSet(ResourceViewSet):

    url = ResourceURL(
        base_regex=r"user",
        lookup_field="pk",
        lookup_regex=r"\d+",
        base_name="user",
    )
