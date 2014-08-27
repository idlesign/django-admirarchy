django-admirarchy
=================
https://github.com/idlesign/django-admirarchy

.. image:: https://badge.fury.io/py/django-admirarchy.png
    :target: http://badge.fury.io/py/django-admirarchy

.. image:: https://pypip.in/d/django-admirarchy/badge.png
        :target: https://crate.io/packages/django-admirarchy


Description
-----------

*Django Admin addon to navigate through hierarchies.*

Have you ever wanted Django Admin to be able to navigate through hierarchies?

Admirarchy does it in an old-school way, just like Norton Commander and Co - one level at a time.


.. code-block:: python

    # admin.py of your application
    from django.contrib import admin

    from .models import MyModel  # Let's say this model represents a hierarchy.
    from admirarchy.toolbox import HierarchicalModelAdmin


    # Inherit from HierarchicalModelAdmin instead of admin.ModelAdmin
    class MyModelAdmin(HierarchicalModelAdmin):

        hierarchy = True  # This enables hierarchy handling.

    admin.site.register(MyModel, MyModelAdmin)


Done. Go navigate %)


Documentation
-------------

http://django-admirarchy.readthedocs.org/
