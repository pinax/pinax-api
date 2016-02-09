from django.core.urlresolvers import reverse
from django.test import TestCase


class Tests(TestCase):

    def setUp(self):
        pass

    def test_something(self):
        r = self.client.get(reverse("user-list"))
        self.assertEqual(r.status_code, 405)
