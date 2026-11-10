from django.contrib import admin

try:
    from django.urls import re_path

except ImportError:
    from django.conf.urls import url as re_path

from pytest_djangoapp.compat import get_urlpatterns


urlpatterns = get_urlpatterns([
    re_path('admin/', admin.site.urls),
])
