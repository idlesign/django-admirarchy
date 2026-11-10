from django.contrib import admin

from admirarchy.toolbox import HierarchicalModelAdmin, NestedSet

from .models import AdjacencyListModel, NestedSetModel


class AdjacencyListModelAdmin(HierarchicalModelAdmin):

    hierarchy = True
    search_fields = ['title']


class NestedSetModelModelAdmin(HierarchicalModelAdmin):

    hierarchy = NestedSet()
    search_fields = ['title']


admin.site.register(AdjacencyListModel, AdjacencyListModelAdmin)
admin.site.register(NestedSetModel, NestedSetModelModelAdmin)
