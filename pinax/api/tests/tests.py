from __future__ import unicode_literals

from ..test import TestCase


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


class TestPagination(TestCase):
    """
    Check the meta["paginator"] response values.
    """

    def setUp(self):
        pass

    def test_empty_collection(self):
        pass

    def test_single_item(self):
        """
        Ensure correct response for a "collection" of one item.
        """
        pass

    def test_multiple_items(self):
        """
        Ensure correct response for a collection of several items.
        """
        pass


class TestPaginationPageSize(TestCase):
    """
    Verify proper operation of "page[size]" pagination in request.GET.
    """

    def setUp(self):
        pass

    def test_one_item_size_zero(self):
        """
        No idea what will happen here!
        """
        pass

    def test_two_items_size_one(self):
        """
        Ensure we see just first item in response.
        """

    def test_two_items_size_two(self):
        """
        Ensure we see both items in response.
        """


class TestPaginationPageNumber(TestCase):
    """
    Verify proper operation of "page[number]" pagination in request.GET.
    """

    def setUp(self):
        pass

    def test_page_zero(self):
        """
        No idea what will happen here!
        """
        pass

    def test_page_negative(self):
        """
        No idea what will happen here!
        """
        pass

    def test_first_page(self):
        """
        Ensure correct items are returned
        """
        pass

    def test_last_page(self):
        """
        Ensure correct items are returned
        """
        pass

    def test_beyond_page(self):
        """
        Ensure error is correct for page exceeding the number of pages.
        """
        pass
