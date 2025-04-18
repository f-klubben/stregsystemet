from django.db.models import Q, Count, Sum
from django.db import models
from collections import defaultdict

import datetime
import pytz

from stregsystem.models import (
    Product,
    Category,
    Member,
    Achievement,
    AchievementMember,
    AchievementTask,
)

def get_new_achievements(member:Member, product:Product, amount = 1): 
    """Gets newly acquired achievements after having bought something"""

    categories = product.categories.values_list('id', flat=True)
    time_now = datetime.datetime.now(tz=pytz.timezone("Europe/Copenhagen"))

    tasks = __filter_achievement_tasks(product, categories, time_now)

    __add_missing_achievement_members(member, tasks)

    achievement_members_in_progress = AchievementMember.objects.filter(
        member_id=member,
        achievement_task__in=tasks,
        completed_at__isnull=True
    )

    __update_progress(product, amount, achievement_members_in_progress)

    completed_achievements = __find_completed_achievements(achievement_members_in_progress, time_now)
    return __convert_achievement_member_to_dict(completed_achievements)


def get_acquired_achievements(member:Member):
    """Gets all acquired achievements for a member"""
    achievement_members = AchievementMember.objects.filter(
        member=member, completed_at__isnull=False
    ).select_related("achievement_task__achievement")

    return __convert_achievement_member_to_dict(achievement_members)


def get_missing_achievements(member:Member):
    """Gets all missing achievements for a member"""
    achievement_members = AchievementMember.objects.filter(
        member=member, completed_at__isnull=True
    ).select_related("achievement_task__achievement")
    
    return __convert_achievement_member_to_dict(achievement_members)


def __convert_achievement_member_to_dict(achievement_members):
    achievement_dicts = []
    
    for am in achievement_members:
        dict = {"title": am.achievement_task.achievement.title,
                "description": am.achievement_task.achievement.description,
                "icon_png": am.achievement_task.achievement.icon_png,
                "goal_count": am.achievement_task.goal_count,
                "progress_count": am.progress_count}
        achievement_dicts.append(dict)

    achievement_dicts = list({a["title"]: a for a in achievement_dicts}.values())
    return achievement_dicts


def __find_completed_achievements(achievement_members_in_progress, time_now):
    
    # Collect all achievement IDs
    achievement_ids = (
        achievement_members_in_progress
        .values_list("achievement_task__achievement_id", flat=True)
        .distinct()
    )

    # Fetch all related AchievementMember objects in one go
    all_related_members = AchievementMember.objects.filter(
        achievement_task__achievement_id__in=achievement_ids
    ).select_related("achievement_task", "achievement_task__achievement")

    # Group by achievement_id
    achievement_groups = defaultdict(list)
    for am in all_related_members:
        achievement_groups[am.achievement_task.achievement_id].append(am)

    acquired = []

    for group in achievement_groups.values():
        if all(am.progress_count >= am.achievement_task.goal_count for am in group):
            for am in group:
                if am.completed_at is None:
                    am.completed_at = time_now
                    acquired.append(am)

    if acquired:
        AchievementMember.objects.bulk_update(acquired, ['completed_at'])

    return acquired


def __update_progress(product, amount, achievement_members_in_progress):
    to_update = []

    for am in achievement_members_in_progress:
        task_type = am.achievement_task.task_type

        if task_type == "balance":
            am.progress_count += amount * (product.price / 100.0)
        else:
            am.progress_count += amount

        to_update.append(am)

    if to_update:
        AchievementMember.objects.bulk_update(to_update, ["progress_count"])


def __add_missing_achievement_members(member, tasks):
    existing = AchievementMember.objects.filter(
        member=member,
        achievement_task__in=tasks
    ).values_list('achievement_task_id', flat=True)

    new_members = []

    for task in tasks:
        if task.id not in existing:
            new_members.append(
                AchievementMember(
                    member=member,
                    achievement_task=task,
                )
            )

    if new_members:
        AchievementMember.objects.bulk_create(new_members)


def __filter_achievement_tasks(product, categories, time_now:datetime):

    final_filter = Q(achievement__weekday=None) | Q(achievement__weekday=time_now.strftime("%A").lower())
    final_filter &= Q(achievement__day_of_month=None) | Q(achievement__day_of_month=time_now.day)
    final_filter &= ((Q(achievement__time_start=None) & Q(achievement__time_end=None)) | 
                     (Q(achievement__time_start__lte=time_now.time()) & Q(achievement__time_end__gte=time_now.time())))
    final_filter &= ((Q(achievement__date_start=None) & Q(achievement__date_end=None)) | 
                     (Q(achievement__date_start__lte=time_now.date()) & Q(achievement__date_end__gte=time_now.date())))

    category_or_product = Q()
    if product:
        category_or_product |= Q(product_id=product)

    for category in categories:
        category_or_product |= Q(category_id=category)

    final_filter &= Q(task_type="any") | Q(task_type="balance") | (Q(task_type="default") & category_or_product)

    return AchievementTask.objects.filter(final_filter)