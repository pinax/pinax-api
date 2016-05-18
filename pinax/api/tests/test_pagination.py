from __future__ import unicode_literals

from django.core.paginator import EmptyPage
from django.core.urlresolvers import reverse
from django.test import RequestFactory

from ..jsonapi import TopLevel
from .. import registry
from .models import (
    Article,
    Author,
)
from .test import TestCase


class TestPagination(TestCase):
    """
    Check the meta["paginator"] response values.
    """
    def setUp(self):
        self.request = RequestFactory()
        self.request.GET = {}
        self.articles_url = reverse("article-list")
        self.article_resource = registry["article"]

    def test_empty_collection(self):
        """
        Verify result with no items in collection.
        """
        resources = self.article_resource.from_queryset(Article.objects.none())
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
        author = Author.objects.create(name="Author")
        item1 = Article.objects.create(title="test 1", author=author)
        resources = self.article_resource.from_queryset(Article.objects.all())
        data = {
            "data": resources,
            "linkage": False
        }
        top_level = TopLevel(**data)
        article_tags_url = reverse("article-tags-relationship-detail", kwargs=dict(pk=item1.pk))
        expected = {
            "jsonapi": {"version": "1.0"},
            "meta": {
                "paginator": {
                    "count": 1,
                    "num_pages": 1
                }
            },
            "data": [
                {
                    "type": "article",
                    "id": str(item1.pk),
                    "attributes": {
                        "title": item1.title,
                    },
                    "relationships": {
                        "tags": {
                            "links": {
                                "self": "{}".format(article_tags_url)
                            },
                            "data": []
                        },
                        "author": {
                            "links": {
                                "self": reverse("article-author-relationship-detail", kwargs=dict(pk=item1.pk))
                            },
                            "data": {
                                "type": "author",
                                "id": str(author.pk)
                            }
                        }
                    }
                }
            ]
        }
        payload = top_level.serializable(request=self.request)

        self.assertResourceGraphEqual(
            expected.pop("data"),
            payload.pop("data")
        )
        # Check that the remaining JSON is identical
        self.assertEqual(expected, payload)
        self.assertEqual(payload, expected)

    def test_multiple_items(self):
        """
        Ensure correct response for a collection of several items.
        """
        author = Author.objects.create(name="Author")
        item1 = Article.objects.create(title="test 1", author=author)
        item2 = Article.objects.create(title="test 2", author=author)
        item3 = Article.objects.create(title="test 3", author=author)
        resources = self.article_resource.from_queryset(Article.objects.all())
        data = {
            "data": resources,
            "linkage": False
        }
        top_level = TopLevel(**data)
        expected = {
            "jsonapi": {"version": "1.0"},
            "meta": {
                "paginator": {
                    "count": 3,
                    "num_pages": 1
                }
            },
            "data": [
                {
                    "type": "article",
                    "id": str(item1.pk),
                    "attributes": {
                        "title": item1.title,
                    },
                    "relationships": {
                        "tags": {
                            "links": {
                                "self": reverse("article-tags-relationship-detail", kwargs=dict(pk=item1.pk))
                            },
                            "data": []
                        },
                        "author": {
                            "links": {
                                "self": reverse("article-author-relationship-detail", kwargs=dict(pk=item1.pk))
                            },
                            "data": {
                                "type": "author",
                                "id": str(author.pk)
                            }
                        }
                    }
                },
                {
                    "type": "article",
                    "id": str(item2.pk),
                    "attributes": {
                        "title": item2.title,
                    },
                    "relationships": {
                        "tags": {
                            "links": {
                                "self": reverse("article-tags-relationship-detail", kwargs=dict(pk=item2.pk))
                            },
                            "data": []
                        },
                        "author": {
                            "links": {
                                "self": reverse("article-author-relationship-detail", kwargs=dict(pk=item2.pk))
                            },
                            "data": {
                                "type": "author",
                                "id": str(author.pk)
                            }
                        }
                    }
                },
                {
                    "type": "article",
                    "id": str(item3.pk),
                    "attributes": {
                        "title": item3.title,
                    },
                    "relationships": {
                        "tags": {
                            "links": {
                                "self": reverse("article-tags-relationship-detail", kwargs=dict(pk=item3.pk))
                            },
                            "data": []
                        },
                        "author": {
                            "links": {
                                "self": reverse("article-author-relationship-detail", kwargs=dict(pk=item3.pk))
                            },
                            "data": {
                                "type": "author",
                                "id": str(author.pk)
                            }
                        }
                    }
                }
            ]
        }
        payload = top_level.serializable(request=self.request)

        self.assertResourceGraphEqual(
            expected.pop("data"),
            payload.pop("data")
        )
        # Check that the remaining JSON is identical
        self.assertEqual(expected, payload)
        self.assertEqual(payload, expected)


class TestPaginationPageSize(TestCase):
    """
    Verify proper operation of "page[size]" pagination in request.GET.
    """
    def setUp(self):
        self.request = RequestFactory()
        self.request.GET = {}
        self.author = Author.objects.create(name="Author")
        self.item1 = Article.objects.create(title="test 1", author=self.author)
        self.item2 = Article.objects.create(title="test 2", author=self.author)
        self.item3 = Article.objects.create(title="test 3", author=self.author)
        self.article_resource = registry["article"]
        resources = self.article_resource.from_queryset(Article.objects.all())
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
        expected = {
            "jsonapi": {"version": "1.0"},
            "meta": {
                "paginator": {
                    "count": 3,
                    "num_pages": 1
                }
            },
            "data": [
                {
                    "type": "article",
                    "id": str(self.item1.pk),
                    "attributes": {
                        "title": self.item1.title,
                    },
                    "relationships": {
                        "tags": {
                            "links": {
                                "self": reverse("article-tags-relationship-detail", kwargs=dict(pk=self.item1.pk))
                            },
                            "data": []
                        },
                        "author": {
                            "links": {
                                "self": reverse("article-author-relationship-detail", kwargs=dict(pk=self.item1.pk))
                            },
                            "data": {
                                "type": "author",
                                "id": str(self.author.pk)
                            }
                        }
                    }
                },
                {
                    "type": "article",
                    "id": str(self.item2.pk),
                    "attributes": {
                        "title": self.item2.title,
                    },
                    "relationships": {
                        "tags": {
                            "links": {
                                "self": reverse("article-tags-relationship-detail", kwargs=dict(pk=self.item2.pk))
                            },
                            "data": []
                        },
                        "author": {
                            "links": {
                                "self": reverse("article-author-relationship-detail", kwargs=dict(pk=self.item2.pk))
                            },
                            "data": {
                                "type": "author",
                                "id": str(self.author.pk)
                            }
                        }
                    }
                },
                {
                    "type": "article",
                    "id": str(self.item3.pk),
                    "attributes": {
                        "title": self.item3.title,
                    },
                    "relationships": {
                        "tags": {
                            "links": {
                                "self": reverse("article-tags-relationship-detail", kwargs=dict(pk=self.item3.pk))
                            },
                            "data": []
                        },
                        "author": {
                            "links": {
                                "self": reverse("article-author-relationship-detail", kwargs=dict(pk=self.item3.pk))
                            },
                            "data": {
                                "type": "author",
                                "id": str(self.author.pk)
                            }
                        }
                    }
                }
            ]
        }
        payload = self.top_level.serializable(request=self.request)

        self.assertResourceGraphEqual(
            expected.pop("data"),
            payload.pop("data")
        )
        # Check that the remaining JSON is identical
        self.assertEqual(expected, payload)
        self.assertEqual(payload, expected)

    def test_page_size_one(self):
        """
        Ensure we see just first item in response.
        """
        self.request.GET["page[size]"] = 1

        expected = {
            "jsonapi": {"version": "1.0"},
            "meta": {
                "paginator": {
                    "count": 3,
                    "num_pages": 3
                }
            },
            "data": [
                {
                    "type": "article",
                    "id": str(self.item1.pk),
                    "attributes": {
                        "title": self.item1.title,
                    },
                    "relationships": {
                        "tags": {
                            "links": {
                                "self": reverse("article-tags-relationship-detail", kwargs=dict(pk=self.item1.pk))
                            },
                            "data": []
                        },
                        "author": {
                            "links": {
                                "self": reverse("article-author-relationship-detail", kwargs=dict(pk=self.item1.pk))
                            },
                            "data": {
                                "type": "author",
                                "id": str(self.author.pk)
                            }
                        }
                    }
                }
            ]
        }

        payload = self.top_level.serializable(request=self.request)

        self.assertResourceGraphEqual(
            expected.pop("data"),
            payload.pop("data")
        )
        # Check that the remaining JSON is identical
        self.assertEqual(expected, payload)
        self.assertEqual(payload, expected)

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
                        "type": "article",
                        "id": str(self.item1.pk),
                        "attributes": {
                            "title": self.item1.title,
                        },
                        "relationships": {
                            "tags": {
                                "links": {
                                    "self": reverse("article-tags-relationship-detail", kwargs=dict(pk=self.item1.pk))
                                },
                                "data": []
                            },
                            "author": {
                                "links": {
                                    "self": reverse("article-author-relationship-detail", kwargs=dict(pk=self.item1.pk))
                                },
                                "data": {
                                    "type": "author",
                                    "id": str(self.author.pk)
                                }
                            }
                        }
                    },
                    {
                        "type": "article",
                        "id": str(self.item2.pk),
                        "attributes": {
                            "title": self.item2.title,
                        },
                        "relationships": {
                            "tags": {
                                "links": {
                                    "self": reverse("article-tags-relationship-detail", kwargs=dict(pk=self.item2.pk))
                                },
                                "data": []
                            },
                            "author": {
                                "links": {
                                    "self": reverse("article-author-relationship-detail", kwargs=dict(pk=self.item2.pk))
                                },
                                "data": {
                                    "type": "author",
                                    "id": str(self.author.pk)
                                }
                            }
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
                        "type": "article",
                        "id": str(self.item1.pk),
                        "attributes": {
                            "title": self.item1.title,
                        },
                        "relationships": {
                            "tags": {
                                "links": {
                                    "self": reverse("article-tags-relationship-detail", kwargs=dict(pk=self.item1.pk))
                                },
                                "data": []
                            },
                            "author": {
                                "links": {
                                    "self": reverse("article-author-relationship-detail", kwargs=dict(pk=self.item1.pk))
                                },
                                "data": {
                                    "type": "author",
                                    "id": str(self.author.pk)
                                }
                            }
                        }
                    },
                    {
                        "type": "article",
                        "id": str(self.item2.pk),
                        "attributes": {
                            "title": self.item2.title,
                        },
                        "relationships": {
                            "tags": {
                                "links": {
                                    "self": reverse("article-tags-relationship-detail", kwargs=dict(pk=self.item2.pk))
                                },
                                "data": []
                            },
                            "author": {
                                "links": {
                                    "self": reverse("article-author-relationship-detail", kwargs=dict(pk=self.item2.pk))
                                },
                                "data": {
                                    "type": "author",
                                    "id": str(self.author.pk)
                                }
                            }
                        }
                    },
                    {
                        "type": "article",
                        "id": str(self.item3.pk),
                        "attributes": {
                            "title": self.item3.title,
                        },
                        "relationships": {
                            "tags": {
                                "links": {
                                    "self": reverse("article-tags-relationship-detail", kwargs=dict(pk=self.item3.pk))
                                },
                                "data": []
                            },
                            "author": {
                                "links": {
                                    "self": reverse("article-author-relationship-detail", kwargs=dict(pk=self.item3.pk))
                                },
                                "data": {
                                    "type": "author",
                                    "id": str(self.author.pk)
                                }
                            }
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
        self.author = Author.objects.create(name="Author")
        self.item1 = Article.objects.create(title="test 1", author=self.author)
        self.item2 = Article.objects.create(title="test 2", author=self.author)
        self.item3 = Article.objects.create(title="test 3", author=self.author)
        self.article_resource = registry["article"]
        resources = self.article_resource.from_queryset(Article.objects.all())
        data = {
            "data": resources,
            "linkage": False
        }
        self.top_level = TopLevel(**data)
        self.author_relationship_url = reverse(
            "article-author-relationship-detail",
            kwargs=dict(pk=self.item1.pk)
        )

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
        expected = {
            "jsonapi": {"version": "1.0"},
            "meta": {
                "paginator": {
                    "count": 3,
                    "num_pages": 3
                }
            },
            "data": [
                {
                    "type": "article",
                    "id": str(self.item1.pk),
                    "attributes": {
                        "title": self.item1.title,
                    },
                    "relationships": {
                        "tags": {
                            "links": {
                                "self": reverse("article-tags-relationship-detail", kwargs=dict(pk=self.item1.pk))
                            },
                            "data": []
                        },
                        "author": {
                            "links": {
                                "self": reverse("article-author-relationship-detail", kwargs=dict(pk=self.item1.pk))
                            },
                            "data": {
                                "type": "author",
                                "id": str(self.author.pk)
                            }
                        }
                    }
                }
            ]
        }
        # verify items
        self.assertResourceGraphEqual(
            expected.pop("data"),
            payload.pop("data")
        )
        # Check that the remaining JSON is identical
        self.assertEqual(expected, payload)

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
                        "type": "article",
                        "id": str(self.item3.pk),
                        "attributes": {
                            "title": self.item3.title,
                        },
                        "relationships": {
                            "tags": {
                                "links": {
                                    "self": reverse("article-tags-relationship-detail", kwargs=dict(pk=self.item3.pk))
                                },
                                "data": []
                            },
                            "author": {
                                "links": {
                                    "self": reverse("article-author-relationship-detail", kwargs=dict(pk=self.item3.pk))
                                },
                                "data": {
                                    "type": "author",
                                    "id": str(self.author.pk)
                                }
                            }
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
