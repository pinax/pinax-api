from __future__ import unicode_literals

from django.core.paginator import EmptyPage
from django.test import RequestFactory

from ..jsonapi import TopLevel
from .models import TestItem
from .resources import TestItemResource
from .test import TestCase


class TestPagination(TestCase):
    """
    Check the meta["paginator"] response values.
    """
    def setUp(self):
        self.request = RequestFactory()
        self.request.GET = {}

    def test_empty_collection(self):
        """
        Verify result with no items in collection.
        """
        resources = TestItemResource.from_queryset(TestItem.objects.none())
        data = {
            "data": resources,
            "linkage": False
        }
        top_level = TopLevel(**data)
        payload = top_level.serializable(request=self.request)
        self.assertEqual(
            payload,
            {
                "jsonapi": {"version": "1.0"},
                "meta": {
                    "paginator": {
                        "count": 0,
                        "num_pages": 1
                    }
                },
                "data": [
                ]
            }
        )

    def test_single_item(self):
        """
        Ensure correct response for a "collection" of one item.
        """
        item1 = TestItem.objects.create(title="test 1")
        resources = TestItemResource.from_queryset(TestItem.objects.all())
        data = {
            "data": resources,
            "linkage": False
        }
        top_level = TopLevel(**data)
        payload = top_level.serializable(request=self.request)
        self.assertEqual(
            payload,
            {
                "jsonapi": {"version": "1.0"},
                "meta": {
                    "paginator": {
                        "count": 1,
                        "num_pages": 1
                    }
                },
                "data": [
                    {
                        "type": "testitem",
                        "id": str(item1.pk),
                        "attributes": {
                            "title": item1.title,
                        },
                    },
                ]
            }
        )

    def test_multiple_items(self):
        """
        Ensure correct response for a collection of several items.
        """
        item1 = TestItem.objects.create(title="test 1")
        item2 = TestItem.objects.create(title="test 2")
        item3 = TestItem.objects.create(title="test 3")
        resources = TestItemResource.from_queryset(TestItem.objects.all())
        data = {
            "data": resources,
            "linkage": False
        }
        top_level = TopLevel(**data)
        payload = top_level.serializable(request=self.request)
        self.assertEqual(
            payload,
            {
                "jsonapi": {"version": "1.0"},
                "meta": {
                    "paginator": {
                        "count": 3,
                        "num_pages": 1
                    }
                },
                "data": [
                    {
                        "type": "testitem",
                        "id": str(item1.pk),
                        "attributes": {
                            "title": item1.title,
                        },
                    },
                    {
                        "type": "testitem",
                        "id": str(item2.pk),
                        "attributes": {
                            "title": item2.title,
                        },
                    },
                    {
                        "type": "testitem",
                        "id": str(item3.pk),
                        "attributes": {
                            "title": item3.title,
                        },
                    },
                ]
            }
        )


class TestPaginationPageSize(TestCase):
    """
    Verify proper operation of "page[size]" pagination in request.GET.
    """
    def setUp(self):
        self.request = RequestFactory()
        self.request.GET = {}
        self.item1 = TestItem.objects.create(title="test 1")
        self.item2 = TestItem.objects.create(title="test 2")
        self.item3 = TestItem.objects.create(title="test 3")
        resources = TestItemResource.from_queryset(TestItem.objects.all())
        data = {
            "data": resources,
            "linkage": False
        }
        self.top_level = TopLevel(**data)

    def test_page_size_zero(self):
        """
        Verify if page[size] == 0, all items are returned anyway.
        """
        self.request.GET["page[size]"] = 0
        payload = self.top_level.serializable(request=self.request)
        self.assertEqual(
            payload,
            {
                "jsonapi": {"version": "1.0"},
                "meta": {
                    "paginator": {
                        "count": 3,
                        "num_pages": 1
                    }
                },
                "data": [
                    {
                        "type": "testitem",
                        "id": str(self.item1.pk),
                        "attributes": {
                            "title": self.item1.title,
                        }
                    },
                    {
                        "type": "testitem",
                        "id": str(self.item2.pk),
                        "attributes": {
                            "title": self.item2.title,
                        }
                    },
                    {
                        "type": "testitem",
                        "id": str(self.item3.pk),
                        "attributes": {
                            "title": self.item3.title,
                        }
                    }
                ]
            }
        )

    def test_page_size_one(self):
        """
        Ensure we see just first item in response.
        """
        self.request.GET["page[size]"] = 1
        payload = self.top_level.serializable(request=self.request)
        self.assertEqual(
            payload,
            {
                "jsonapi": {"version": "1.0"},
                "meta": {
                    "paginator": {
                        "count": 3,
                        "num_pages": 3
                    }
                },
                "data": [
                    {
                        "type": "testitem",
                        "id": str(self.item1.pk),
                        "attributes": {
                            "title": self.item1.title,
                        }
                    }
                ]
            }
        )

    def test_page_size_two(self):
        """
        Ensure we see two items in response.
        """
        self.request.GET["page[size]"] = 2
        payload = self.top_level.serializable(request=self.request)
        self.assertEqual(
            payload,
            {
                "jsonapi": {"version": "1.0"},
                "meta": {
                    "paginator": {
                        "count": 3,
                        "num_pages": 2
                    }
                },
                "data": [
                    {
                        "type": "testitem",
                        "id": str(self.item1.pk),
                        "attributes": {
                            "title": self.item1.title,
                        }
                    },
                    {
                        "type": "testitem",
                        "id": str(self.item2.pk),
                        "attributes": {
                            "title": self.item2.title,
                        }
                    }
                ]
            }
        )

    def test_page_size_five(self):
        """
        Ensure we see two items in response.
        """
        self.request.GET["page[size]"] = 5
        payload = self.top_level.serializable(request=self.request)
        self.assertEqual(
            payload,
            {
                "jsonapi": {"version": "1.0"},
                "meta": {
                    "paginator": {
                        "count": 3,
                        "num_pages": 1
                    }
                },
                "data": [
                    {
                        "type": "testitem",
                        "id": str(self.item1.pk),
                        "attributes": {
                            "title": self.item1.title,
                        }
                    },
                    {
                        "type": "testitem",
                        "id": str(self.item2.pk),
                        "attributes": {
                            "title": self.item2.title,
                        }
                    },
                    {
                        "type": "testitem",
                        "id": str(self.item3.pk),
                        "attributes": {
                            "title": self.item3.title,
                        }
                    }
                ]
            }
        )


class TestPaginationPageNumber(TestCase):
    """
    Verify proper operation of "page[number]" pagination in request.GET.
    """
    def setUp(self):
        self.request = RequestFactory()
        self.request.GET = {}
        self.item1 = TestItem.objects.create(title="test 1")
        self.item2 = TestItem.objects.create(title="test 2")
        self.item3 = TestItem.objects.create(title="test 3")
        resources = TestItemResource.from_queryset(TestItem.objects.all())
        data = {
            "data": resources,
            "linkage": False
        }
        self.top_level = TopLevel(**data)

    def test_page_zero(self):
        """
        Ensure expected exception for page number == 0.
        """
        self.request.GET["page[size]"] = 1
        self.request.GET["page[number]"] = 0
        with self.assertRaises(EmptyPage):
            self.top_level.serializable(request=self.request)

    def test_page_negative(self):
        """
        Ensure expected exception for page number == -1.
        """
        self.request.GET["page[size]"] = 1
        self.request.GET["page[number]"] = -1
        with self.assertRaises(EmptyPage):
            self.top_level.serializable(request=self.request)

    def test_first_page(self):
        """
        Ensure correct items are returned
        """
        self.request.GET["page[size]"] = 1
        self.request.GET["page[number]"] = 1
        payload = self.top_level.serializable(request=self.request)
        self.assertEqual(
            payload,
            {
                "jsonapi": {"version": "1.0"},
                "meta": {
                    "paginator": {
                        "count": 3,
                        "num_pages": 3
                    }
                },
                "data": [
                    {
                        "type": "testitem",
                        "id": str(self.item1.pk),
                        "attributes": {
                            "title": self.item1.title,
                        }
                    }
                ]
            }
        )

    def test_last_page(self):
        """
        Ensure correct items are returned
        """
        self.request.GET["page[size]"] = 1
        self.request.GET["page[number]"] = 3
        payload = self.top_level.serializable(request=self.request)
        self.assertEqual(
            payload,
            {
                "jsonapi": {"version": "1.0"},
                "meta": {
                    "paginator": {
                        "count": 3,
                        "num_pages": 3
                    }
                },
                "data": [
                    {
                        "type": "testitem",
                        "id": str(self.item3.pk),
                        "attributes": {
                            "title": self.item3.title,
                        }
                    }
                ]
            }
        )

    def test_beyond_page(self):
        """
        Ensure expected exception for page exceeding the number of pages.
        """
        self.request.GET["page[size]"] = 1
        self.request.GET["page[number]"] = 5
        with self.assertRaises(EmptyPage):
            self.top_level.serializable(request=self.request)

