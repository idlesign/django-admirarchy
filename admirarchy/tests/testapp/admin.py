from django.contrib import admin

from .models import AdjacencyListModel
from admirarchy.toolbox import HierarchicalModelAdmin


class MyModelAdmin(HierarchicalModelAdmin):

    hierarchy = True


admin.site.register(AdjacencyListModel, MyModelAdmin)
