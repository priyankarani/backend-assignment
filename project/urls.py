
from django.conf.urls import url
from django.urls import include, path
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^accounts/', include('authtools.urls')),
    path('', include('homes.urls')),
]
