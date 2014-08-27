Advanced usage
==============

Here are some words on more advanced ``admirarchy`` usage.


Adjacent lists
--------------

For hierarchies described through adjacent lists you can explicitly define name
of a field in your model containing parent item identifier:


.. code-block:: python

    from django.contrib import admin

    from .models import MyModel
    from admirarchy.toolbox import HierarchicalModelAdmin, AdjacentList


    class MyModelAdmin(HierarchicalModelAdmin):

        hierarchy = AdjacentList('upper')  # That says MyModel uses `upper` field to store parent ID.


    admin.site.register(MyModel, MyModelAdmin)


