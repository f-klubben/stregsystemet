from django.contrib import admin
from .models import KioskItem, KioskImageItem, KioskWebsiteItem
from polymorphic.admin import PolymorphicParentModelAdmin, PolymorphicChildModelAdmin, PolymorphicChildModelFilter


def set_active_kiosk_item(modeladmin, request, queryset):
    queryset.update(active=True)


set_active_kiosk_item.short_description = "Make selected kiosk items active"


def set_inactive_kiosk_item(modeladmin, request, queryset):
    queryset.update(active=False)


set_inactive_kiosk_item.short_description = "Make selected kiosk items inactive"


@admin.register(KioskImageItem)
class KioskImageItemAdmin(PolymorphicChildModelAdmin):
    base_model = KioskImageItem

@admin.register(KioskWebsiteItem)
class KioskWebsiteItemAdmin(PolymorphicChildModelAdmin):
    base_model = KioskWebsiteItem


@admin.register(KioskItem)
class ModelAParentAdmin(PolymorphicParentModelAdmin):
    base_model = KioskImageItem
    child_models = (KioskImageItem, KioskWebsiteItem)
    search_fields = ('name',)
    list_display = ('active', 'name', 'notes', 'ordering', 'uploaded_date')
    list_filter = ('active',PolymorphicChildModelFilter)
    list_display_links = ('active', 'name', 'notes', 'ordering', 'uploaded_date')
    actions = [set_active_kiosk_item, set_inactive_kiosk_item]

