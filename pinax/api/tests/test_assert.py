from __future__ import unicode_literals

from .test import TestCase


class TestAssertResourceGraph(TestCase):

    def setUp(self):
        self.first_item = {
            "type": "lorem",
            "id": "33",
            "attributes": {
                "quantity": 1
            },
            "links": {
                "self": "http://testserver/lorem/33"
            },
            "relationships": {
                "product": {
                    "links": {
                        "self": "http://testserver/relationships/product"
                    },
                    "data": {
                        "id": "44",
                        "type": "product"
                    }
                }
            }
        }

        self.second_item = {
            "type": "product",
            "id": "44",
            "attributes": {
                "name": "Excelsior",
                "slug": "excelsior",
            },
            "links": {"self": "http://testserver/products/44"},
            "relationships": {
                "category": {
                    "data": {
                        "type": "category",
                        "id": "12",
                    },
                    "links": {
                        "self": "http://testserver/products/44/relationships/category",
                    }
                }
            }
        }

        self.third_item = {
            "type": "ipsum",
            "id": "55",
            "attributes": {
                "words": 42
            },
            "links": {
                "self": "http://testserver/ipsum/55"
            }
        }

        self.fourth_item = {
            "type": "product",
            "id": "44",
            "attributes": {
                "name": "Excelsiore",  # slightly different name than in self.second_item
                "slug": "excelsiore",
            },
            "links": {"self": "http://testserver/products/44"},
            "relationships": {
                "category": {
                    "data": {
                        "type": "category",
                        "id": "12",
                    },
                    "links": {
                        "self": "http://testserver/products/44/relationships/category",
                    }
                }
            }
        }

    def test_unordered_identical(self):

        a = [self.first_item, self.second_item]
        b = [self.second_item, self.first_item]
        self.assertResourceGraphEqual(a, b)

    def test_unequal_count(self):
        """
        Ensure we catch when lists have different amount of resources.
        """
        a = [self.first_item, self.second_item]
        b = [self.first_item]
        with self.assertRaises(AssertionError):
            self.assertResourceGraphEqual(a, b)

    def test_different_resources(self):
        """
        Ensure we catch when lists contain different resources.
        """
        a = [self.first_item, self.second_item]
        b = [self.first_item, self.third_item]
        with self.assertRaises(AssertionError):
            self.assertResourceGraphEqual(a, b)

    def test_different_items(self):
        """
        Ensure we catch when item count is identical
        and item resource ID is identical but
        items themselves are different.
        """
        a = [self.first_item, self.second_item]
        b = [self.first_item, self.fourth_item]
        with self.assertRaises(AssertionError):
            self.assertResourceGraphEqual(a, b)
