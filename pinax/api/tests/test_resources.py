import json
import mock

from django.contrib.auth.models import AnonymousUser
from django.core.urlresolvers import reverse

from pinax import api

from .models import (
    Article,
    Author,
)


class ArticleViewSetTestCase(api.TestCase):

    def test_get_empty_collection(self):
        """
        Ensure correct `list` response when no Articles exist.
        """
        collection_url = reverse("article-list")

        with mock.patch("pinax.api.authentication.Anonymous.authenticate", autospec=True) as mock_authenticate:
            mock_authenticate.return_value = AnonymousUser()
            response = self.client.get(collection_url)
            payload = json.loads(response.content.decode("utf-8"))
            expected = {
                "jsonapi": {"version": "1.0"},
                "links": {
                    "self": "http://testserver{}".format(collection_url),
                },
                "meta": {
                    "paginator": {
                        "count": 0,
                        "num_pages": 1
                    }
                },
                "data": [],
            }
            self.assertEqual(expected, payload)

    def test_get_collection(self):
        """
        Ensure correct `list` response when one Article exists.
        """
        author = Author.objects.create(name="First Author")
        article = Article.objects.create(title="Test Article", author=author)

        collection_url = reverse("article-list")
        detail_url = reverse("article-detail", kwargs=dict(pk=article.pk))
        tag_relationship_url = reverse(
            "article-tags-relationship-detail",
            kwargs=dict(pk=article.pk)
        )
        author_relationship_url = reverse(
            "article-author-relationship-detail",
            kwargs=dict(pk=article.pk)
        )

        with mock.patch("pinax.api.authentication.Anonymous.authenticate", autospec=True) as mock_authenticate:
            mock_authenticate.return_value = AnonymousUser()
            response = self.client.get(collection_url)
            payload = json.loads(response.content.decode("utf-8"))
            expected = {
                "jsonapi": {"version": "1.0"},
                "links": {
                    "self": "http://testserver{}".format(collection_url),
                },
                "meta": {
                    "paginator": {
                        "count": 1,
                        "num_pages": 1
                    }
                },
                "data": [
                    {
                        "type": "article",
                        "id": str(article.pk),
                        "attributes": {
                            "title": article.title,
                        },
                        "links": {
                            "self": "http://testserver{}".format(detail_url),
                        },
                        "relationships": {
                            "tags": {
                                "links": {
                                    "self":  "http://testserver{}".format(tag_relationship_url)
                                },
                                "data": []
                            },
                            "author": {
                                "links": {
                                    "self":  "http://testserver{}".format(author_relationship_url)
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
            # verify items
            self.assertResourceGraphEqual(
                expected.pop("data"),
                payload.pop("data")
            )
            self.assertEqual(expected, payload)

    def test_get_article(self):
        """
        Ensure correct `detail` response for an Article.
        """
        author = Author.objects.create(name="First Author")
        article = Article.objects.create(title="Test Article", author=author)

        detail_url = reverse("article-detail", kwargs=dict(pk=article.pk))
        tag_relationship_url = reverse(
            "article-tags-relationship-detail",
            kwargs=dict(pk=article.pk)
        )
        author_relationship_url = reverse(
            "article-author-relationship-detail",
            kwargs=dict(pk=article.pk)
        )

        with mock.patch("pinax.api.authentication.Anonymous.authenticate", autospec=True) as mock_authenticate:
            mock_authenticate.return_value = AnonymousUser()
            response = self.client.get(detail_url)
            payload = json.loads(response.content.decode("utf-8"))
            expected = {
                "jsonapi": {"version": "1.0"},
                "data": {
                    "type": "article",
                    "id": str(article.pk),
                    "attributes": {
                        "title": article.title,
                    },
                    "links": {
                        "self": "http://testserver{}".format(detail_url)
                    },
                    "relationships": {
                        "tags": {
                            "links": {
                                "self":  "http://testserver{}".format(tag_relationship_url)
                            },
                            "data": []
                        },
                        "author": {
                            "links": {
                                "self":  "http://testserver{}".format(author_relationship_url)
                            },
                            "data": {
                                "type": "author",
                                "id": str(author.pk)
                            }
                        }
                    }
                },
                "links": {
                    "self": "http://testserver{}".format(detail_url)
                },
            }
            self.assertEqual(expected, payload)

    def test_create(self):

        author = Author.objects.create(name="Article Author")
        post_data = {
            "data": {
                "type": "article",
                "attributes": {
                    "title": "First Article"
                },
                "relationships": {
                    "author": {
                        "data": {
                            "type": "author",
                            "id": str(author.pk)
                        }
                    }
                }
            }
        }
        with mock.patch("pinax.api.authentication.Anonymous.authenticate", autospec=True) as mock_authenticate:
            mock_authenticate.return_value = AnonymousUser()
            collection_url = reverse("article-list")
            response = self.client.post(
                collection_url,
                data=json.dumps(post_data),
                content_type="application/vnd.api+json"
            )
            self.assertEqual(response.status_code, 201)
            self.assertEqual(response["Content-Type"], "application/vnd.api+json")

            article = Article.objects.get()
            # Article1 Relationship URLs
            article_tags_url = reverse("article-tags-relationship-detail", kwargs=dict(pk=article.pk))
            article_author_url = reverse("article-author-relationship-detail", kwargs=dict(pk=article.pk))

            payload = json.loads(response.content.decode("utf-8"))
            expected = {
                "jsonapi": {"version": "1.0"},
                "data": {
                    "type": "article",
                    "id": str(article.pk),
                    "links": {
                        "self": "http://testserver{}".format(reverse("article-detail", kwargs=dict(pk=article.pk)))
                    },
                    "attributes": {
                        "title": article.title,
                    },
                    "relationships": {
                        "tags": {
                            "data": [],
                            "links": {
                                "self": "http://testserver{}".format(article_tags_url)
                            }
                        },
                        "author": {
                            "data": {
                                "type": "author",
                                "id": str(author.pk)
                            },
                            "links": {
                                "self": "http://testserver{}".format(article_author_url)
                            }
                        }
                    }
                },
                "links": {
                    "self": "http://testserver{}".format(collection_url)
                }
            }
            self.assertEqual(expected, payload)
