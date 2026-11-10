Advanced usage
==============

Here are some words on more advanced ``admirarchy`` usage.



Adjacency lists
---------------

For hierarchies described through adjacency lists you can explicitly define a name
of a field in your model containing parent item identifier (defaults to ``parent``):


.. code-block:: python

    from django.contrib import admin

    from admirarchy.toolbox import HierarchicalModelAdmin, AdjacencyList

    from .models import MyModel


    @admin.register(MyModel)
    class MyModelAdmin(HierarchicalModelAdmin):

        hierarchy = AdjacencyList('upper')  # That says MyModel uses `upper` field to store parent ID.



Nested sets
-----------

For hierarchies described through nested sets you can explicitly define names
of fields containing left and right set limits, and nesting level (defaults to ``lft``, ``rgt`` and ``level`` respectively):


.. code-block:: python

    from django.contrib import admin

    from admirarchy.toolbox import HierarchicalModelAdmin, NestedSet

    from .models import MyModel


    @admin.register(MyModel)
    class MyModelAdmin(HierarchicalModelAdmin):

        # That says MyModel uses has 'left_border', 'right_border', 'depth' to describe nesting.
        hierarchy = NestedSet('left_border', 'right_border', 'depth')

