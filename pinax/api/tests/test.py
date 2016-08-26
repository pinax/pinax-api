from django.test import TestCase as BaseTestCase


class TestCase(BaseTestCase):

    maxDiff = None

    def assertResourceGraphEqual(self, a, b):
        """
        Compare two lists of JSON:API resources.
        """
        self.assertTrue(len(a) == len(b), "Mismatched list lengths")

        a_graph, b_graph = {}, {}
        for i in a:
            a_graph[(i["type"], i["id"])] = i
        for i in b:
            b_graph[(i["type"], i["id"])] = i
        for resource_id in a_graph:
            self.assertIn(
                resource_id,
                b_graph,
                "Resource {} is missing from second list".format(resource_id)
            )
            self.assertEqual(a_graph[resource_id], b_graph[resource_id])
