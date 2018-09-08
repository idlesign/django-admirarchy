from django.contrib import admin
from django.conf.urls import url

from pytest_djangoapp.compat import get_urlpatterns


urlpatterns = get_urlpatterns([
    url('admin/', admin.site.urls),
])
