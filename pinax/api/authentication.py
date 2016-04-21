def add(backends):
    def decorator(func):
        func.authentication = backends
        return func
    return decorator


class Anonymous(object):

    def authenticate(self, request):
        if not request.user.is_authenticated():
            from django.contrib.auth.models import AnonymousUser
            return AnonymousUser()
