from django.contrib.auth.models import AnonymousUser


def add(backends):
    def decorator(func):
        func.authentication = backends
        return func
    return decorator


class Anonymous(object):

    def authenticate(self, request):
        return AnonymousUser()
