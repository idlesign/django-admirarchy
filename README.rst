django-admirarchy
=================
https://github.com/idlesign/django-admirarchy

.. image:: https://idlesign.github.io/lbc/py2-lbc.svg
   :target: https://idlesign.github.io/lbc/
   :alt: LBC Python 2

----

|release| |lic| |ci| |coverage| |health|

.. |release| image:: https://img.shields.io/pypi/v/django-admirarchy.svg
    :target: https://pypi.python.org/pypi/django-admirarchy

.. |lic| image:: https://img.shields.io/pypi/l/django-admirarchy.svg
    :target: https://pypi.python.org/pypi/django-admirarchy

.. |ci| image:: https://img.shields.io/travis/idlesign/django-admirarchy/master.svg
    :target: https://travis-ci.org/idlesign/django-admirarchy

.. |coverage| image:: https://img.shields.io/coveralls/idlesign/django-admirarchy/master.svg
    :target: https://coveralls.io/r/idlesign/django-admirarchy

.. |health| image:: https://landscape.io/github/idlesign/django-admirarchy/master/landscape.svg?style=flat
    :target: https://landscape.io/github/idlesign/django-admirarchy/master


Description
-----------

*Django Admin addon to navigate through hierarchies.*

Have you ever wanted Django Admin to be able to navigate through hierarchies?

Without existing models modifications? Yeah!

Admirarchy does it in an old-school way, just like Norton Commander and Co - one level at a time.

Hierarchies described as adjacency lists and nested sets are supported.


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
