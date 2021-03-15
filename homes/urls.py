from django.urls import include, path
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'houses', views.HouseViewSet)
router.register(r'rooms', views.RoomViewSet)
router.register(r'lights', views.LightViewSet)
router.register(r'thermostats', views.ThermostatViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('api/', include(router.urls)),
    path(
        'api-auth/',
        include('rest_framework.urls', namespace='rest_framework')
    )
]
