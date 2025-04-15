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

    tasks = __filter_achievement_tasks(product, categories)

    __add_missing_achievement_members(member, tasks)

    achievement_members_in_progress = AchievementMember.objects.filter(
        member_id=member,
        achievement_task__in=tasks,
        # completed_at__isnull=True
    )

    __update_progress(product, amount, achievement_members_in_progress)

    return __find_completed_achievements(achievement_members_in_progress)


def get_acquired_achievements(member:Member):
    """Gets all acquired achievements for a member"""

    return AchievementMember.objects.filter(member=member, completed_at__isnull=False)

def get_missing_achievements(member:Member):
    """Gets all missing achievements for a member"""

    return AchievementMember.objects.filter(member=member, completed_at__isnull=True)


def __find_completed_achievements(achievement_members_in_progress):
    
    acquired_achievements = []

    for am in achievement_members_in_progress:
        related_achievements = AchievementMember.objects.filter(
            achievement_task__achievement=am.achievement_task.achievement
        )

        # Check if all tasks for each achievement are completed
        if all(am2.progress_count >= am2.achievement_task.goal_count for am2 in related_achievements):
            am.completed_at = datetime.datetime.now(tz=pytz.timezone("Europe/Copenhagen"))
            am.save()

            acquired_achievements.append(am)

    return acquired_achievements


def __update_progress(product, amount, achievement_members_in_progress):
    for am in achievement_members_in_progress:
        task_type = am.achievement_task.task_type

        if task_type == "balance":
            am.progress_count += amount * (product.price / 100.0)
        else:
            am.progress_count += amount

        am.save()


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


def __filter_achievement_tasks(product, categories):
    any_filter = Q(task_type="any")
    balance_filter = Q(task_type="balance")

    default_filter = Q(task_type="default")

    category_or_product = Q()
    if product:
        category_or_product |= Q(product_id=product)
    for category in categories:
        category_or_product |= Q(category_id=category)

    default_filter &= category_or_product

    final_filter = default_filter | any_filter | balance_filter
    
    return AchievementTask.objects.filter(final_filter)