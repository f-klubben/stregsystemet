from django.contrib import admin

from razzia.models import Razzia, RazziaEntry
from stregsystem.admin import BaseAdmin


@admin.register(Razzia)
class RazziaAdmin(BaseAdmin):
    search_fields = ('name',)
    list_filter = ('start_date',)
    date_hierarchy = 'start_date'

    def _get_fields_to_display(self) -> list[str]:
        return [
            'name',
            'turns_per_member',
            'turn_interval',
        ] + super()._get_fields_to_display()

    def _get_fields_to_display_as_readonly(self) -> list[str]:
        return [
            'start_date',
        ] + super()._get_fields_to_display_as_readonly()


@admin.register(RazziaEntry)
class RazziaEntryAdmin(BaseAdmin):
    def _get_fields_to_display(self) -> list[str]:
        return [
            'id',
            'razzia',
            'member',
        ] + super()._get_fields_to_display()
