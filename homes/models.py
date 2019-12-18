
from model_utils import Choices

from django.db import models


class NameBaseModel(models.Model):
    """
    Base model with common fields.
    """
    name = models.CharField(max_length=200, help_text='Name')

    class Meta:
        abstract = True


class House(NameBaseModel):
    """
    Store details about a house.
    """
    name = models.CharField(max_length=200, help_text='Name of the house.')

    def __str__(self):
        return self.name


class Thermostat(NameBaseModel):
    """
    Store thermostat data.
    """
    house = models.ForeignKey(House, related_name='thermostats', on_delete=models.CASCADE, help_text='Related house.')
    MODES = Choices(
        ('off', 'Off'),
        ('fan', 'Fan'),
        ('auto', 'Auto'),
        ('cool', 'Cool'),
        ('heat', 'Heat'))
    mode = models.CharField(choices=MODES, default=MODES.off, max_length=5, help_text='Current mode of the thermostat.')
    current_temperature = models.DecimalField(
        decimal_places=2,
        max_digits=5,
        help_text='Current temperature at the thermostat.')
    temperature_set_point = models.DecimalField(
        decimal_places=2,
        max_digits=5,
        help_text='Temperature set point.')

    def __str__(self):
        return self.name


class Room(NameBaseModel):
    """
    Store room information.
    """
    house = models.ForeignKey(House, related_name='rooms', on_delete=models.CASCADE, help_text='Related house.')
    current_temperature = models.DecimalField(
        decimal_places=2,
        max_digits=5,
        help_text='Current temperature at the thermostat.')

    def __str__(self):
        return self.name


class Light(NameBaseModel):
    """
    Store room information.
    """
    room = models.ForeignKey(Room, related_name='lights', on_delete=models.CASCADE, help_text='Related room.')
    STATE = Choices(
        ('on', 'On'),
        ('off', 'Off'))
    state = models.CharField(choices=STATE, default=STATE.off, max_length=3, help_text='Current state of the light.')

    def __str__(self):
        return self.name
