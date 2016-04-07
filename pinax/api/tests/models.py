from django.db import models

class TestItem(models.Model):
    title = models.CharField(max_length=100)
