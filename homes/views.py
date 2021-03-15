from rest_framework import viewsets

from .serializers import (
    HouseSerializer, RoomSerializer, LightSerializer, ThermostatSerializer
)
from .models import House, Room, Light, Thermostat


class HouseViewSet(viewsets.ModelViewSet):
    queryset = House.objects.all()
    serializer_class = HouseSerializer


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer


class LightViewSet(viewsets.ModelViewSet):
    queryset = Light.objects.all()
    serializer_class = LightSerializer


class ThermostatViewSet(viewsets.ModelViewSet):
    queryset = Thermostat.objects.all()
    serializer_class = ThermostatSerializer
