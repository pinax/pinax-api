from django.test import TestCase as BaseTestCase


class TestCase(BaseTestCase):

    def assertGraphEqual(self, a, b):
        """
        Compare two lists of JSON:API resources.
        """
        a_graph, b_graph = {}, {}
        for i in a:
            a_graph[(i["type"], i["id"])] = i
        for i in b:
            b_graph[(i["type"], i["id"])] = i
        self.assertTrue(len(a) == len(b), "Mismatched included lengths")
        for rid in a_graph:
            self.assertIn(rid, b_graph, "{} is missing from other included".format(rid))
            self.assertEqual(a_graph[rid], b_graph[rid])
