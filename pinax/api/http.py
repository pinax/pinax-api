from __future__ import unicode_literals

import json

from django.http.response import HttpResponse, HttpResponseRedirectBase


class Response(HttpResponse):

    def __init__(self, data, *args, **kwargs):
        super(Response, self).__init__(content=json.dumps(data), *args, **kwargs)
        self["Content-Type"] = "application/vnd.api+json"


class Redirect(HttpResponseRedirectBase):
    pass
