Advanced usage
==============

Here are some words on more advanced ``admirarchy`` usage.



Adjacency lists
---------------

For hierarchies described through adjacency lists you can explicitly define a name
of a field in your model containing parent item identifier (defaults to ``parent``):


.. code-block:: python

    from django.contrib import admin

    from .models import MyModel
    from admirarchy.toolbox import HierarchicalModelAdmin, AdjacencyList


    class MyModelAdmin(HierarchicalModelAdmin):

        hierarchy = AdjacencyList('upper')  # That says MyModel uses `upper` field to store parent ID.


    admin.site.register(MyModel, MyModelAdmin)



Nested sets
-----------

For hierarchies described through nested sets you can explicitly define names
of fields containing left and right set limits, and nesting level (defaults to ``lft``, ``rgt`` and ``level`` respectively):


.. code-block:: python

    from django.contrib import admin

    from .models import MyModel
    from admirarchy.toolbox import HierarchicalModelAdmin, NestedSet


    class MyModelAdmin(HierarchicalModelAdmin):

        # That says MyModel uses has 'left_border', 'right_border', 'depth' to describe nesting.
        hierarchy = NestedSet('left_border', 'right_border', 'depth')


    admin.site.register(MyModel, MyModelAdmin)
