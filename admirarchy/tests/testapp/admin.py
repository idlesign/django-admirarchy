from django.contrib import admin

from admirarchy.toolbox import HierarchicalModelAdmin, NestedSet

from .models import AdjacencyListModel, NestedSetModel


class AdjacencyListModelAdmin(HierarchicalModelAdmin):

    hierarchy = True


class NestedSetModelModelAdmin(HierarchicalModelAdmin):

    hierarchy = NestedSet()


admin.site.register(AdjacencyListModel, AdjacencyListModelAdmin)
admin.site.register(NestedSetModel, NestedSetModelModelAdmin)
