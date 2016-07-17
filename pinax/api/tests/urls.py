import itertools

from .endpoints import (
    ArticleEndpointSet,
    ArticleTagEndpointSet,
    AuthorEndpointSet,
)


urlpatterns = []
urlpatterns.extend(itertools.chain(
    ArticleEndpointSet.as_urls(),
    ArticleTagEndpointSet.as_urls(),
    AuthorEndpointSet.as_urls(),
))
