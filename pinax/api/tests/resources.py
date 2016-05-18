from pinax import api

from .models import (
    Article,
    ArticleTag,
    Author,
)


@api.register
class ArticleTagResource(api.Resource):

    api_type = "articletag"
    model = ArticleTag
    attributes = [
        api.Attribute(name="tag", obj_attr="name"),
    ]

    @property
    def id(self):
        return self.obj.name


@api.register
class AuthorResource(api.Resource):

    api_type = "author"
    model = Author
    attributes = [
        "name",
    ]

    @property
    def id(self):
        return self.obj.pk


@api.register
class ArticleResource(api.Resource):

    api_type = "article"
    model = Article
    attributes = [
        "title",
    ]
    relationships = {
        "tags": api.Relationship("articletag", collection=True),
        "author": api.Relationship("author"),
    }

    @property
    def id(self):
        return self.obj.pk
