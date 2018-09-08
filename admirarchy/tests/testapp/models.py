from django.db import models


class AdjacencyListModel(models.Model):

    title = models.CharField(max_length=100)

    parent = models.ForeignKey(
        'self', related_name='%(class)s_parent', on_delete=models.CASCADE, db_index=True, null=True, blank=True)

    def __str__(self):
        return 'adjacencylistmodel_%s' % self.title


class NestedSetModel(models.Model):

    title = models.CharField(max_length=100)

    lft = models.IntegerField(db_index=True)
    rgt = models.IntegerField(db_index=True)
    level = models.IntegerField(db_index=True)

    def __str__(self):
        return 'nestedsetmodel_%s' % self.title
