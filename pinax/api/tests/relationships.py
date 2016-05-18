from pinax import api
from pinax.api.exceptions import ErrorResponse

from .models import Article


class ArticleTagCollectionEndpointSet(api.RelationshipEndpointSet):

    middleware = {
        "authentication": [
            api.authentication.Anonymous(),
        ]
    }

    def prepare(self):
        if "pk" in self.kwargs:
            self.article = self.get_article(self.kwargs["pk"])
        self.resource_class = api.registry["articletag"]

    def get_article(self, pk):
        """
        Return Article matching `pk`, or raise exception.
        """
        article = next(iter(Article.objects.filter(pk=pk)), None)
        if not article:
            raise ErrorResponse(
                **self.error_response_kwargs("Article {} not found".format(pk), status=404)
            )
        return article

    def create(self, request, pk):
        """
        Identifier: Add tag(s) to an Article
         """
        with self.validate(self.resource_class, collection=True) as resources:
            tags = [resource.obj.name for resource in resources]
            for tag in tags:
                self.article.tags.create(name=tag)
            return self.render(None)

    def update(self, request, pk):
        """
        Identifier: Replace all tags associated with an Article
        """
        with self.validate(self.resource_class, collection=True) as resources:
            tags = [resource.obj.name for resource in resources]
            self.article.tags.clear()
            for tag in tags:
                self.article.tags.create(name=tag)
            return self.render(None)

    def retrieve(self, request, pk):
        """
        Identifier: List tags for an Article
        """
        tags = self.article.tags.all()
        return self.render(self.resource_class.from_queryset(tags))

    def destroy(self, request, pk):
        """
        Identifier: Remove tag(s) from an Article
        """
        with self.validate(self.resource_class, collection=True) as resources:
            tags = [resource.obj.name for resource in resources]
            self.article.tags.filter(name__in=tags).delete()
            return self.render_delete()


class ArticleAuthorEndpointSet(api.RelationshipEndpointSet):
    pass