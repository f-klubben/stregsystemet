from django.contrib import admin

from .models import KioskItem


def set_active_kiosk_item(modeladmin, request, queryset):
    queryset.update(active=True)


set_active_kiosk_item.short_description = "Gør valgte kiosk items aktive"


def set_inactive_kiosk_item(modeladmin, request, queryset):
    queryset.update(active=False)


set_inactive_kiosk_item.short_description = "Gør valgte kiosk items inaktive"


class KioskItemAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = ('active', 'name', 'notes', 'ordering', 'uploaded_date')
    list_filter = ('active',)
    list_display_links = ('active', 'name', 'notes', 'ordering', 'uploaded_date')
    actions = [set_active_kiosk_item, set_inactive_kiosk_item]


admin.site.register(KioskItem, KioskItemAdmin)
