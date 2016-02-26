from django.contrib.auth.models import AnonymousUser


class Anonymous(object):

    def authenticate(self):
        return AnonymousUser()
