
from model_utils import Choices, FieldTracker

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import (
    GenericForeignKey, GenericRelation
)
from django.core.exceptions import ValidationError


MODES = Choices(
    ('off', 'Off'),
    ('fan', 'Fan'),
    ('auto', 'Auto'),
    ('cool', 'Cool'),
    ('heat', 'Heat')
)

STATE = Choices(
    ('on', 'On'),
    ('off', 'Off')
)

TYPE = Choices(
    ('State', 'State'),
    ('Temperature', 'Temperature'),
    ('Mode', 'Mode'),
    ('Temperature set point', 'Temperature set point'),
)


class NameBaseModel(models.Model):
    """
    Base model with common fields.
    """
    name = models.CharField(max_length=200, help_text='Name')
    created = models.DateTimeField(
        auto_now_add=True,
        help_text="Date and time this object was created."
    )
    modified = models.DateTimeField(
        auto_now=True,
        help_text="Date and time this object was last modified."
    )

    class Meta:
        abstract = True


equipments = (
    models.Q(app_label='homes', model='light') |
    models.Q(app_label='homes', model='room') |
    models.Q(app_label='homes', model='thermostat')
)


class TrackRecord(NameBaseModel):
    """
    A Model to keep track of each change of state for light,
    thermostat and room temperature
    """
    target_content_type = models.ForeignKey(
        ContentType, limit_choices_to=equipments, on_delete=models.CASCADE
    )
    target_object_id = models.PositiveIntegerField()
    target = GenericForeignKey('target_content_type', 'target_object_id')

    state_type = models.CharField(
        choices=TYPE, max_length=25,
        help_text='Type of the state that has been changed'
    )

    from_state = models.CharField(
        max_length=6,
        help_text='Thermostat mode, light state or room '
        'temperature value, that has been changed'
    )

    to_state = models.CharField(
        max_length=6,
        help_text='New value for thermostat mode, light state or room '
        'temperature'
    )

    def save(self, *args, **kwargs):
        self.full_clean()

        return super(TrackRecord, self).save(*args, **kwargs)

    def clean(self):
        if self.target_content_type and not self.target:
            raise ValidationError(
                str(self.target_content_type) +
                ' with id ' + str(self.target_object_id) + " does not exist!"
            )

    def __str__(self):
        if self.target:
            return "[%s] %s has been changed from %s to %s at %s" % (
                self.target.name, self.state_type, self.from_state,
                self.to_state, self.modified
            )


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
    house = models.ForeignKey(
        House, related_name='thermostats',
        on_delete=models.CASCADE, help_text='Related house.'
    )

    mode = models.CharField(
        choices=MODES, default=MODES.off, max_length=5,
        help_text='Current mode of the thermostat.'
    )
    current_temperature = models.DecimalField(
        decimal_places=2,
        max_digits=5,
        help_text='Current temperature at the thermostat.'
    )
    temperature_set_point = models.DecimalField(
        decimal_places=2,
        max_digits=5,
        help_text='Temperature set point.'
    )
    tracker = FieldTracker()
    track_records = GenericRelation(
        TrackRecord, object_id_field='target_object_id',
        content_type_field='target_content_type',
        related_query_name="Thermostat track records"
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):

        if self.pk is None:
            return super(Thermostat, self).save(*args, **kwargs)

        # If its an update to the record and mode or temperature is changed,
        # Keep a track record for each change in temperature or mode
        if self.tracker.has_changed("current_temperature"):
            TrackRecord.objects.create(
                name=self.name,
                state_type="Temperature",
                target_content_type=ContentType.objects.get_for_model(
                    Thermostat
                ),
                target_object_id=self.pk,
                from_state=self.tracker.previous("current_temperature"),
                to_state=self.current_temperature,
            )
        if self.tracker.has_changed("temperature_set_point"):
            TrackRecord.objects.create(
                name=self.name,
                state_type="Temperature set point",
                target_content_type=ContentType.objects.get_for_model(
                    Thermostat
                ),
                target_object_id=self.pk,
                from_state=self.tracker.previous("temperature_set_point"),
                to_state=self.temperature_set_point,
            )

        if self.tracker.has_changed("mode"):
            TrackRecord.objects.create(
                name=self.name,
                state_type="Mode",
                target_content_type=ContentType.objects.get_for_model(
                    Thermostat
                ),
                target_object_id=self.pk,
                from_state=self.tracker.previous("mode"),
                to_state=self.mode,
            )

        return super(Thermostat, self).save(*args, **kwargs)


class Room(NameBaseModel):
    """
    Store room information.
    """
    house = models.ForeignKey(
        House, related_name='rooms', on_delete=models.CASCADE,
        help_text='Related house.'
    )
    current_temperature = models.DecimalField(
        decimal_places=2,
        max_digits=5,
        help_text='Current temperature at the thermostat.'
    )
    tracker = FieldTracker()
    track_records = GenericRelation(
        TrackRecord, object_id_field='target_object_id',
        content_type_field='target_content_type',
        related_query_name="Room track records"
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):

        # If its an update to the record and current temperature is changed,
        # Keep a track record for each change in temperature
        if self.pk is not None and \
                self.tracker.has_changed("current_temperature"):
            TrackRecord.objects.create(
                name=self.name,
                state_type="Temperature",
                target_content_type=ContentType.objects.get_for_model(Room),
                target_object_id=self.pk,
                from_state=self.tracker.previous("current_temperature"),
                to_state=self.current_temperature,
            )

        return super(Room, self).save(*args, **kwargs)


class Light(NameBaseModel):
    """
    Store room information.
    """
    room = models.ForeignKey(
        Room, related_name='lights', on_delete=models.CASCADE,
        help_text='Related room.'
    )

    state = models.CharField(
        choices=STATE, default=STATE.off, max_length=3,
        help_text='Current state of the light.'
    )
    tracker = FieldTracker()
    track_records = GenericRelation(
        TrackRecord, object_id_field='target_object_id',
        content_type_field='target_content_type',
        related_query_name="Light track records"
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):

        # If its an update to the record and state is changed, Add Track
        # Record for this to track each change of state
        if self.pk is not None and self.tracker.has_changed("state"):
            TrackRecord.objects.create(
                name=self.name,
                state_type="State",
                target_content_type=ContentType.objects.get_for_model(Light),
                target_object_id=self.pk,
                from_state=self.tracker.previous("state"),
                to_state=self.state,
            )

        return super(Light, self).save(*args, **kwargs)
