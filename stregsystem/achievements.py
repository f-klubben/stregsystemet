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

def get_acquired_achievements(member:Member, product:Product = None, amount = 1): 

    if product:
        categories = product.categories.values_list('id', flat=True)

    tasks = filter_achievement_tasks(product, categories)

    add_missing_achievement_members(member, tasks)

    # Does there exist a ahievementMember which refers to the achievementTasks?
    achievement_members_in_progress = AchievementMember.objects.filter(
        member_id=member,
        achievement_task__in=tasks,
        completed_at__isnull=True
    )

    for am in achievement_members_in_progress:
        task_type = am.achievement_task.task_type

        if task_type == "balance":
            am.progress_count += amount * (product.price / 100.0)
        else:
            am.progress_count += amount

        am.save()


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


def add_missing_achievement_members(member, tasks):
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


def filter_achievement_tasks(product, categories):
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