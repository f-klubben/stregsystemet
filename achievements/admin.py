from datetime import datetime

import pytz
from achievements.forms import AchievementForm
from achievements.models import Achievement, AchievementTask, AchievementComplete, AchievementConstraint
from django.contrib import admin
from django.utils.html import format_html
from stregsystem.admin import BaseAdmin
from django.conf import settings


class AchievementAdmin(BaseAdmin):
    form = AchievementForm

    search_fields = ['title', 'description']

    def _get_fields_to_display(self):
        return [
            'title',
            'description',
            'get_icon',
            'get_active_from_or_active_duration',
        ] + super()._get_fields_to_display()

    fieldsets = (
        (None, {'fields': ('title', 'description')}),
        (None, {'fields': (('icon', 'existing_icons'),)}),
        (None, {'fields': ('tasks', 'constraints')}),
        (None, {'fields': (('active_from', 'active_duration'),)}),
    )

    def get_icon(self, obj):
        if obj.icon:
            filename = obj.icon.name.rsplit('/', 1)[-1]
            filename = filename.rsplit('\\', 1)[-1]
            return format_html('<img src="{}" style="height: 20px;"/> {}', obj.icon.url, filename)
        return "-"

    get_icon.short_description = 'Icon'

    def get_active_from_or_active_duration(self, obj):
        if obj.active_from is not None:
            return f"Active From: {obj.active_from.strftime('%Y-%m-%d %H:%M:%S')}"
        elif obj.active_duration is not None:
            return f"Active Duration: {obj.active_duration}"

    get_active_from_or_active_duration.short_description = "Active-From / -Duration"

    @admin.action(description="Set Active From to now")
    def set_active_from_to_now(self, request, queryset):
        for obj in queryset:
            obj.active_from = datetime.now(tz=pytz.timezone(settings.TIME_ZONE))
            obj.full_clean()
            obj.save()

    @admin.action(description="Set Active From to None")
    def set_active_from_to_null(self, request, queryset):
        for obj in queryset:
            obj.active_from = None
            obj.full_clean()
            obj.save()

    actions = [set_active_from_to_now, set_active_from_to_null]


class AchievementTaskAdmin(BaseAdmin):
    def _get_fields_to_display(self):
        return [
            'notes',
            'task_type',
            'goal_value',
            'get_product',
            'category',
        ] + super()._get_fields_to_display()

    def get_product(self, obj):
        if obj.product:
            name = str(obj.product)
            return name[:20] + "..." if len(name) > 20 else name
        return ""

    get_product.short_description = "Product"


class AchievementCompleteAdmin(BaseAdmin):

    valid_lookups = ['member', 'achievement']
    search_fields = ['member__username', 'achievement__title', 'achievement__description', 'completed_at']

    def _get_fields_to_display(self):
        return [
            'get_username',
            'get_achievement_title',
            'get_achievement_description',
            'completed_at',
        ] + super()._get_fields_to_display()

    def get_username(self, obj):
        return obj.member.username

    def get_achievement_title(self, obj):
        return obj.achievement.title

    get_achievement_title.short_description = 'Achievement Title'

    def get_achievement_description(self, obj):
        return obj.achievement.description

    get_achievement_description.short_description = 'Achievement Description'


class AchievementConstraintAdmin(BaseAdmin):
    def _get_fields_to_display(self):
        return [
            'notes',
            'month_start',
            'month_end',
            'day_start',
            'day_end',
            'time_start',
            'time_end',
            'weekday',
        ] + super()._get_fields_to_display()

    fieldsets = (
        (None, {'fields': ['notes']}),
        (
            None,
            {
                'fields': ['month_start', 'month_end'],
            },
        ),
        (
            None,
            {
                'fields': ['day_start', 'day_end'],
            },
        ),
        (
            None,
            {
                'fields': ['time_start', 'time_end'],
            },
        ),
        (
            None,
            {
                'fields': ['weekday'],
            },
        ),
    )


admin.site.register(Achievement, AchievementAdmin)
admin.site.register(AchievementTask, AchievementTaskAdmin)
admin.site.register(AchievementComplete, AchievementCompleteAdmin)
admin.site.register(AchievementConstraint, AchievementConstraintAdmin)
