from django.contrib import admin

from razzia.models import Razzia, RazziaEntry


@admin.register(Razzia)
class RazziaAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'turns_per_member', 'created_at')
    search_fields = ('name',)
    list_filter = ('start_date',)
    date_hierarchy = 'start_date'
    readonly_fields = ('created_at', 'updated_at', 'start_date')


admin.site.register(RazziaEntry)
