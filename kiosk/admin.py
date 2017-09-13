from django.contrib import admin

from .models import KioskItem


def set_active_kiosk_item(modeladmin, request, queryset):
    queryset.update(active=True)


set_active_kiosk_item.short_description = "Make selected kiosk items active"


def set_inactive_kiosk_item(modeladmin, request, queryset):
    queryset.update(active=False)


set_inactive_kiosk_item.short_description = "Make selected kiosk items inactive"


class KioskItemAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = ('name', 'active')
    list_filter = ('active',)
    list_display_links = ('name', 'active')
    actions = [set_active_kiosk_item, set_inactive_kiosk_item]


# Register your models here.
admin.site.register(KioskItem, KioskItemAdmin)
