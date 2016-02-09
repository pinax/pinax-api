import itertools

from .viewsets import UserViewSet


urlpatterns = []
urlpatterns.extend(itertools.chain(
    UserViewSet.as_urls(),
))
