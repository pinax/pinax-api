from __future__ import unicode_literals

from django.contrib.auth.models import User

from pinax.api import ResourceURL, ResourceViewSet


class UserViewSet(ResourceViewSet):

    url = ResourceURL(
        base_regex=r"user",
        lookup_field="pk",
        lookup_regex=r"\d+",
        base_name="user",
    )

    def list(self, request):
        users = User.objects.all()
        return self.render(users, attributes=["username"])
