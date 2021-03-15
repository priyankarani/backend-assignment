from rest_framework import serializers
from homes.models import House, Thermostat, Room, Light


class HouseSerializer(serializers.ModelSerializer):
    thermostats = serializers.SerializerMethodField(required=False)
    rooms = serializers.SerializerMethodField(required=False)

    class Meta:
        model = House
        fields = ['id', 'name', 'thermostats', 'rooms']

    def get_thermostats(self, obj):
        return [t.id for t in Thermostat.objects.filter(house__id=obj.id)]

    def get_rooms(self, obj):
        return [room.id for room in Room.objects.filter(house__id=obj.id)]


class ThermostatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Thermostat
        fields = '__all__'


class RoomSerializer(serializers.ModelSerializer):
    lights = serializers.SerializerMethodField(required=False)

    class Meta:
        model = Room
        fields = ['id', 'name', 'house', 'current_temperature', 'lights']

    def get_lights(self, obj):
        return [light.id for light in Light.objects.filter(room__id=obj.id)]


class LightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Light
        fields = '__all__'
