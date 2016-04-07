from pinax import api

from .models import TestItem


@api.register
class TestItemResource(api.Resource):

    api_type = "testitem"
    model = TestItem
    attributes = [
        "title",
    ]

    @property
    def id(self):
        return self.obj.pk
