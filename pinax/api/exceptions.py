from .http import Response


class ErrorResponse(Exception):

    def __init__(self, *args, **kwargs):
        self.response = Response(*args, **kwargs)
        super(ErrorResponse, self).__init__("ErrorResponse must be caught and returned to client.")
