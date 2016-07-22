import json
from unittest import mock

from django.contrib.auth.models import AnonymousUser
from django.core.urlresolvers import reverse

from pinax import api

from .models import (
    Article,
    ArticleTag,
    Author,
)


class ArticleTagsViewSetTestCase(api.TestCase):

    def setUp(self):
        super(ArticleTagsViewSetTestCase, self).setUp()

        self.author = Author.objects.create(name="First Author")
        self.article1 = Article.objects.create(title="First Article", author=self.author)
        # Create another Article
        self.article2 = Article.objects.create(title="Second Article", author=self.author)

        # Article1 Relationship URLs
        self.article_tags_url = reverse("article-tags-relationship-detail", kwargs=dict(pk=self.article1.pk))
        self.article_author_url = reverse("article-author-relationship-detail", kwargs=dict(pk=self.article1.pk))

    def test_create(self):
        """
        Create two Article tags.
        """
        new_tag = "Pinax"
        another_new_tag = "Kel"
        post_data = {
            "data": [
                {
                    "type": "articletag",
                    "attributes": {
                        "tag": new_tag,
                    }
                },
                {
                    "type": "articletag",
                    "attributes": {
                        "tag": another_new_tag,
                    }
                }
            ]
        }
        with mock.patch("pinax.api.authentication.Anonymous.authenticate", autospec=True) as mock_authenticate:
            mock_authenticate.return_value = AnonymousUser()

            response = self.client.post(
                self.article_tags_url,
                data=json.dumps(post_data),
                content_type="application/vnd.api+json"
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response["Content-Type"], "application/vnd.api+json")

            payload = json.loads(response.content.decode("utf-8"))
            self.assertEqual(
                payload,
                {
                    "jsonapi": {"version": "1.0"},
                    "links": {
                        "self": "http://testserver{}".format(self.article_tags_url)
                    }
                }
            )
            tags = ArticleTag.objects.filter(article=self.article1).values_list("name", flat=True)
            self.assertIn(new_tag, tags)
            self.assertIn(another_new_tag, tags)

    def test_retrieve(self):
        """
        Retrieve all Article tags.
        """
        # Create two tags for article1.
        first_tag = "Pinax"
        ArticleTag.objects.create(name=first_tag, article=self.article1)
        second_tag = "Kel"
        ArticleTag.objects.create(name=second_tag, article=self.article1)

        with mock.patch("pinax.api.authentication.Anonymous.authenticate", autospec=True) as mock_authenticate:
            mock_authenticate.return_value = AnonymousUser()

            response = self.client.get(
                self.article_tags_url,
                content_type="application/vnd.api+json"
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response["Content-Type"], "application/vnd.api+json")
            payload = json.loads(response.content.decode("utf-8"))

            expected = {
                "jsonapi": {"version": "1.0"},
                "meta": {
                    "paginator": {
                        "count": 2,
                        "num_pages": 1
                    }
                },
                "data": [
                    {
                        "type": "articletag",
                        "id": first_tag
                    },
                    {
                        "type": "articletag",
                        "id": second_tag
                    }
                ],
                "links": {
                    "self": "http://testserver{}".format(self.article_tags_url)
                }
            }

            # verify items
            self.assertResourceGraphEqual(
                expected.pop("data"),
                payload.pop("data")
            )
            # Check that the remaining JSON is identical
            self.assertEqual(expected, payload)

    def test_destroy(self):
        """
        Destroy an Article tag.
        """
        # Create a tag which should remain.
        remain_tag = "Pinax"
        ArticleTag.objects.create(name=remain_tag, article=self.article1)

        # Create a tag for removal.
        remove_tag = "Kel"
        ArticleTag.objects.create(name=remove_tag, article=self.article1)

        post_data = {
            "data": [
                {
                    "type": "articletag",
                    "attributes": {
                        "tag": remove_tag,
                    }
                }
            ]
        }

        with mock.patch("pinax.api.authentication.Anonymous.authenticate", autospec=True) as mock_authenticate:
            mock_authenticate.return_value = AnonymousUser()

            response = self.client.delete(
                self.article_tags_url,
                data=json.dumps(post_data),
                content_type="application/vnd.api+json"
            )
            self.assertEqual(response.status_code, 204)
            self.assertEqual(response["Content-Type"], "application/vnd.api+json")

            article_tags = ArticleTag.objects.filter(article=self.article1).values_list("name", flat=True)
            self.assertNotIn(remove_tag, article_tags)
            self.assertIn(remain_tag, article_tags)

    def test_get_all(self):
        """
        Get all ArticleTags.
        """
        # Create a tag for each Article.
        first_tag = "Pinax"
        ArticleTag.objects.create(name=first_tag, article=self.article1)
        second_tag = "Kel"
        ArticleTag.objects.create(name=second_tag, article=self.article2)

        with mock.patch("pinax.api.authentication.Anonymous.authenticate", autospec=True) as mock_authenticate:
            mock_authenticate.return_value = AnonymousUser()

            response = self.client.get(
                reverse("articletag-list"),
                content_type="application/vnd.api+json"
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response["Content-Type"], "application/vnd.api+json")
            payload = json.loads(response.content.decode("utf-8"))

            expected = {
                "jsonapi": {"version": "1.0"},
                "meta": {
                    "paginator": {
                        "count": 2,
                        "num_pages": 1
                    }
                },
                "data": [
                    {
                        "type": "articletag",
                        "id": first_tag,
                        "attributes": {
                            "tag": first_tag,
                        },
                        "links": {
                            "self": "http://testserver{}".format(reverse("articletag-detail", kwargs=dict(tag=first_tag)))
                        }
                    },
                    {
                        "type": "articletag",
                        "id": second_tag,
                        "attributes": {
                            "tag": second_tag,
                        },
                        "links": {
                            "self": "http://testserver{}".format(reverse("articletag-detail", kwargs=dict(tag=second_tag)))
                        }
                    }
                ],
                "links": {
                    "self": "http://testserver{}".format(reverse("articletag-list"))
                }
            }

            # verify items
            self.assertResourceGraphEqual(
                expected.pop("data"),
                payload.pop("data")
            )
            # Check that the remaining JSON is identical
            self.assertEqual(expected, payload)

    def test_update(self):
        """
        Ensure we can completely replace all Article tags.
        """
        # Create several tags which will get replaced.
        first_tag = "Pinax"
        ArticleTag.objects.create(name=first_tag, article=self.article1)
        second_tag = "Kel"
        ArticleTag.objects.create(name=second_tag, article=self.article1)

        new_tag = "Futurama"
        another_new_tag = "Archer"
        post_data = {
            "data": [
                {
                    "type": "articletag",
                    "attributes": {
                        "tag": new_tag,
                    }
                },
                {
                    "type": "articletag",
                    "attributes": {
                        "tag": another_new_tag,
                    }
                }
            ]
        }
        with mock.patch("pinax.api.authentication.Anonymous.authenticate", autospec=True) as mock_authenticate:
            mock_authenticate.return_value = AnonymousUser()

            response = self.client.patch(
                self.article_tags_url,
                data=json.dumps(post_data),
                content_type="application/vnd.api+json"
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response["Content-Type"], "application/vnd.api+json")

            payload = json.loads(response.content.decode("utf-8"))
            self.assertEqual(
                payload,
                {
                    "jsonapi": {"version": "1.0"},
                    "links": {
                        "self": "http://testserver{}".format(self.article_tags_url)
                    }
                }
            )

            business_tags = ArticleTag.objects.filter(article=self.article1).values_list("name", flat=True)
            self.assertSetEqual(set([new_tag, another_new_tag]), set(list(business_tags)))

    def test_get_article_matching_tag(self):
        """
        """
        # Create a separate tag for each Article
        first_tag = "Pinax"
        ArticleTag.objects.create(name=first_tag, article=self.article1)

        second_tag = "Kel"
        ArticleTag.objects.create(name=second_tag, article=self.article2)

        # Create a third tag used in both Articles.
        third_tag = "Club"
        ArticleTag.objects.create(name=third_tag, article=self.article1)
        ArticleTag.objects.create(name=third_tag, article=self.article2)

        with mock.patch("pinax.api.authentication.Anonymous.authenticate", autospec=True) as mock_authenticate:
            mock_authenticate.return_value = AnonymousUser()

            response = self.client.get(
                "{}?tag={}".format(reverse("article-list"), first_tag),
                content_type="application/vnd.api+json"
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response["Content-Type"], "application/vnd.api+json")
            payload = json.loads(response.content.decode("utf-8"))

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
                        "id": str(self.article1.pk),
                        "attributes": {
                            "title": self.article1.title,
                        },
                        "relationships": {
                            "tags": {
                                "data": [
                                    {
                                        "type": "articletag",
                                        "id": first_tag,
                                    },
                                    {
                                        "type": "articletag",
                                        "id": third_tag,
                                    }
                                ],
                                "links": {
                                    "self": "http://testserver{}".format(self.article_tags_url)
                                }
                            },
                            "author": {
                                "links": {
                                    "self": "http://testserver{}".format(self.article_author_url)
                                },
                                "data": {
                                    "type": "author",
                                    "id": str(self.author.pk)
                                }
                            }
                        },
                        "links": {
                            "self": "http://testserver{}".format(reverse("article-detail", kwargs=dict(pk=self.article1.pk)))
                        }
                    }
                ],
                "links": {
                    "self": "http://testserver{}".format(reverse("article-list"))
                }
            }

            # verify items
            self.assertResourceGraphEqual(
                expected["data"][0]["relationships"]["tags"].pop("data"),
                payload["data"][0]["relationships"]["tags"].pop("data")
            )

            self.assertResourceGraphEqual(
                expected.pop("data"),
                payload.pop("data")
            )
            # Check that the remaining JSON is identical
            self.assertEqual(expected, payload)
