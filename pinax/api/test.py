from django.test import TestCase as BaseTestCase


class TestCase(BaseTestCase):

    def assertUnorderedListEqual(self, a, b):
        """
        Compare two unordered and unhashable lists.
        Ensure the same number of identical elements exist in each list.
        O(n^2) complexity.
        """
        return len(a) == len(b) and all(a.count(i) == b.count(i) for i in a)
