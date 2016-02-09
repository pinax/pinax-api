from __future__ import unicode_literals

import json

from django.core.urlresolvers import reverse
from django.test import TestCase


class Tests(TestCase):

    def setUp(self):
        pass

    def test_something(self):
        r = self.client.get(reverse("user-list"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Content-Type"], "application/vnd.api+json")
        self.assertDictEqual(
            {
                "jsonapi": {"version": "1.0"},
                "links": {
                    "self": "http://testserver/user/",
                },
                "data": [],
            },
            json.loads(r.content),
        )
