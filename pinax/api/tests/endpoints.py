
from pinax import api

from .relationships import (
    ArticleTagCollectionEndpointSet,
    ArticleAuthorEndpointSet,
)
from .resources import (
    ArticleResource,
    ArticleTagResource,
    AuthorResource,
)


@api.bind(resource=ArticleResource)
class ArticleEndpointSet(api.DjangoModelEndpointSetMixin, api.ResourceEndpointSet):
    """
    Handle Article retrieval.
    """
    url = api.url(
        base_name="article",
        base_regex=r"articles",
        lookup={
            "field": "pk",
            "regex": r"\d+"
        }
    )
    relationships = {
        "tags": ArticleTagCollectionEndpointSet,
        "author": ArticleAuthorEndpointSet,
    }
    middleware = {
        "authentication": [
            api.authentication.Anonymous(),
        ]
    }

    def create(self, request):
        with self.validate(self.resource_class) as resource:
            resource.save()
            return self.render_create(resource)

    def list(self, request):
        """
        Identifier: List all Articles, optionally filtered by tag
        """
        qs = self.get_queryset()
        tag_querystring = request.GET.get("tag", "")
        if tag_querystring:
            qs = qs.filter(articletag__name__in=[tag_querystring])
        return self.render(self.resource_class.from_queryset(qs))

    def retrieve(self, request, pk):
        """
        Identifier: Retrieve an Article
        """
        resource = self.resource_class(obj=self.obj)
        return self.render(resource)

    def update(self, request, pk):
        """
        Update an Article
        """
        with self.validate(self.resource_class, obj=self.obj) as resource:
            resource.save()
            return self.render(resource)

    def destroy(self, request, pk):
        """
        Delete an Article
        """
        self.obj.delete()
        return self.render_delete()


@api.bind(resource=ArticleTagResource)
class ArticleTagEndpointSet(api.DjangoModelEndpointSetMixin, api.ResourceEndpointSet):
    """
    Handle ArticleTag retrieval.
    """

    url = api.url(
        base_name="articletag",
        base_regex=r"articletags",
        lookup={
            "field": "tag",
            "regex": r"\w+"
        }
    )
    middleware = {
        "authentication": [
            api.authentication.Anonymous(),
        ]
    }

    def list(self, request):
        """
        Identifier: List all tags
        """
        ArticleTagResource = api.registry["articletag"]
        return self.render(ArticleTagResource.from_queryset(self.get_queryset()))

    def retrieve(self, request, pk):
        """
        Identifier: Retrieve a tag
        """
        resource = self.resource_class(self.obj)
        return self.render(resource)


@api.bind(resource=AuthorResource)
class AuthorEndpointSet(api.DjangoModelEndpointSetMixin, api.ResourceEndpointSet):
    """
    Handle Author retrieval.
    """

    url = api.url(
        base_name="author",
        base_regex=r"authors",
        lookup={
            "field": "pk",
            "regex": r"\d+"
        }
    )
    middleware = {
        "authentication": [
            api.authentication.Anonymous(),
        ]
    }

    def list(self, request):
        """
        Identifier: List all Authors
        """
        AuthorResource = api.registry["author"]
        return self.render(AuthorResource.from_queryset(self.get_queryset()))

    def retrieve(self, request, pk):
        """
        Identifier: Retrieve an Author
        """
        resource = self.resource_class(self.obj)
        return self.render(resource)
