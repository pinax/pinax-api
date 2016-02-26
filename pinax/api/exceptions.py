from __future__ import unicode_literals

from .http import Response


class ErrorResponse(Exception):

    def __init__(self, *args, **kwargs):
        self.response = Response(*args, **kwargs)
        super(ErrorResponse, self).__init__("ErrorResponse must be caught and returned to client.")


class SerializationError(Exception):
    pass


class AuthenticationFailed(Exception):
    pass
