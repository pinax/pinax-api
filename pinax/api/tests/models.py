from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Article(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(Author)

    @property
    def tags(self):
        for tag in self.articletag_set.all():
            yield tag


class ArticleTag(models.Model):
    article = models.ForeignKey(Article)
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name
