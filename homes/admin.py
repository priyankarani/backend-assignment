from django.contrib import admin
from django.contrib.contenttypes.models import ContentType

from .models import House, Thermostat, Room, Light, TrackRecord


class CustomListFilter(admin.SimpleListFilter):
    title = ('Equipments')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'equipments'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return (
            ('Light', 'Light'),
            ('Room', 'Room'),
            ('Thermostat', 'Thermostat'),
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        if not self.value():
            return queryset.all()
        return queryset.filter(
            target_content_type=ContentType.objects.get_for_model(
                eval(self.value())
            )
        )


class TrackRecordAdmin(admin.ModelAdmin):  # pragma: no cover
    search_fields = ['name']
    date_hierarchy = 'modified'
    ordering = ('-modified',)
    list_filter = [CustomListFilter]

    def has_add_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        fields = []
        if obj:
            fields = [field.name for field in self.model._meta.get_fields()]
        return fields

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """
        Hide save button on change_form page
        """
        extra_context = extra_context or {}
        extra_context['show_save_and_add_another'] = False
        extra_context['show_save_and_continue'] = False
        extra_context['show_save'] = False
        return super(TrackRecordAdmin, self).change_view(
            request, object_id, form_url, extra_context=extra_context
        )


admin.site.register(House)
admin.site.register(Thermostat)
admin.site.register(Room)
admin.site.register(Light)
admin.site.register(TrackRecord, TrackRecordAdmin)
