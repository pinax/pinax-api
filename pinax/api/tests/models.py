from django.db import models


class ArticleTag(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Author(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Article(models.Model):
    title = models.CharField(max_length=100)
    author = models.ForeignKey(Author)
    tags = models.ManyToManyField(ArticleTag)
