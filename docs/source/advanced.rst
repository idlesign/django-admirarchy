Advanced usage
==============

Here are some words on more advanced ``admirarchy`` usage.


Adjacency lists
---------------

For hierarchies described through adjacency lists you can explicitly define name
of a field in your model containing parent item identifier:


.. code-block:: python

    from django.contrib import admin

    from .models import MyModel
    from admirarchy.toolbox import HierarchicalModelAdmin, AdjacencyList


    class MyModelAdmin(HierarchicalModelAdmin):

        hierarchy = AdjacencyList('upper')  # That says MyModel uses `upper` field to store parent ID.


    admin.site.register(MyModel, MyModelAdmin)


