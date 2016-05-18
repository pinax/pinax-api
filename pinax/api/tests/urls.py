import itertools

from .viewsets import (
    ArticleViewSet,
    ArticleTagViewSet,
    AuthorViewSet,
)


urlpatterns = []
urlpatterns.extend(itertools.chain(
    ArticleViewSet.as_urls(),
    ArticleTagViewSet.as_urls(),
    AuthorViewSet.as_urls(),
))
