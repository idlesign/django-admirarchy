from django.db import models


class AdjacencyListModel(models.Model):

    title = models.CharField(max_length=100)

    parent = models.ForeignKey(
        'self', related_name='%(class)s_parent', on_delete=models.CASCADE, db_index=True, null=True, blank=True)

    def __str__(self):
        return 'adjlist_%s' % self.title
