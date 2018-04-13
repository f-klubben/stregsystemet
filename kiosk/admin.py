from django.contrib import admin
from polymorphic.admin import PolymorphicParentModelAdmin, PolymorphicChildModelAdmin, PolymorphicChildModelFilter

from .models import KioskItem, KioskImage, KioskVideo


def set_active_kiosk_item(modeladmin, request, queryset):
    queryset.update(active=True)


set_active_kiosk_item.short_description = "Make selected kiosk items active"


def set_inactive_kiosk_item(modeladmin, request, queryset):
    queryset.update(active=False)


set_inactive_kiosk_item.short_description = "Make selected kiosk items inactive"


class KioskItemChildAdmin(PolymorphicChildModelAdmin):
    base_model = KioskItem
    search_fields = ('name',)
    list_display = ('active', 'name', 'notes', 'ordering', 'uploaded_date')
    list_filter = ('active',)
    list_display_links = ('active', 'name', 'notes', 'ordering', 'uploaded_date')
    actions = [set_active_kiosk_item, set_inactive_kiosk_item]

@admin.register(KioskImage)
class ModelImageAdmin(KioskItemChildAdmin):
    base_model = KioskItem

@admin.register(KioskVideo)
class ModelVideoAdmin(KioskItemChildAdmin):
    base_model = KioskItem

@admin.register(KioskItem)
class KioskItemParentAdmin(PolymorphicParentModelAdmin):
    base_model = KioskItem
    child_models = (KioskImage, KioskVideo)
    search_fields = ('name',)
    list_filter = (PolymorphicChildModelFilter, 'active')
    list_display = ('active', 'name', 'notes', 'ordering', 'uploaded_date')
    list_display_links = ('active', 'name', 'notes', 'ordering', 'uploaded_date')
