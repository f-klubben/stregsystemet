from django.db.models import Q, Count, Sum
from django.db import models
from collections import defaultdict

from datetime import datetime, timedelta
import pytz

from stregsystem.models import (
    Product,
    Category,
    Sale,
    Member,
    Achievement,
    AchievementMember,
    AchievementTask,
)

def get_new_achievements(member:Member, product:Product, amount=1): 
    """Gets newly acquired achievements after having bought something"""

    _add_missing_achievement_members(member)

    categories = product.categories.values_list('id', flat=True)
    now = datetime.now(tz=pytz.timezone("Europe/Copenhagen"))

    tasks = _filter_achievement_tasks(product, categories, now)

    achievement_members_in_progress = AchievementMember.objects.filter(
        member_id=member,
        achievement_task__in=tasks,
        # completed_at__isnull=True
    ).select_related("achievement_task", "achievement_task__product", "achievement_task__category")

    completed_achievements = _find_completed_achievements(achievement_members_in_progress, member, now)

    return _convert_achievement_member_to_dict(completed_achievements)


def get_acquired_achievements(member:Member):
    """Gets all acquired achievements for a member"""
    achievement_members = AchievementMember.objects.filter(
        member=member, completed_at__isnull=False
    ).select_related("achievement_task__achievement")

    return _convert_achievement_member_to_dict(achievement_members)


def get_missing_achievements(member:Member):
    """Gets all missing achievements for a member"""
    achievement_members = AchievementMember.objects.filter(
        member=member, completed_at__isnull=True
    ).select_related("achievement_task__achievement")
    
    return _convert_achievement_member_to_dict(achievement_members)


def get_user_leaderboard_position(member: Member):
    """
    Returns the top percentage that the member is in 
    based on number of completed achievements among all users.
    Example: 0.1 means top 10%.
    """
    # Count completed achievements per user
    leaderboard = (
        AchievementMember.objects
        .filter(completed_at__isnull=False)
        .values('member')
        .annotate(total=Count('id'))
        .order_by('-total')
    )

    total_members = leaderboard.count()
    if total_members == 0:
        return 1.0  # Everyone's equal, user is at 100%

    # Find member's rank
    for index, entry in enumerate(leaderboard):
        if entry['member'] == member.id:
            position = index + 1  # 1-based rank
            break
    else:
        return 1.0  # Member has no achievements, so last place

    # Calculate top percentage
    return position / total_members


def _convert_achievement_member_to_dict(achievement_members):
    achievement_dicts = []
    
    for am in achievement_members:
        dict = {"title": am.achievement_task.achievement.title,
                "description": am.achievement_task.achievement.description,
                "icon_png": am.achievement_task.achievement.icon_png,
                "goal_count": am.achievement_task.goal_count}
        achievement_dicts.append(dict)

    achievement_dicts = list({a["title"]: a for a in achievement_dicts}.values())
    return achievement_dicts


def _find_completed_achievements(achievement_members, member, now):
            
    task_to_sales = _filter_sales(achievement_members, member)

    achievement_groups = defaultdict(list)
    for am in achievement_members:
        achievement_groups[am.achievement_task.achievement_id].append(am)

    acquired = []
    for group in achievement_groups.values():
        sales = task_to_sales[am.achievement_task]

        sales_count = sales.count()
        if all(sales_count >= am.achievement_task.goal_count for am in group):
            for am in group:
                if am.completed_at is None:
                    am.completed_at = now
                    acquired.append(am)

    if acquired:
        AchievementMember.objects.bulk_update(acquired, ['completed_at'])

    return acquired


def _add_missing_achievement_members(member):
    
    missing_tasks = AchievementTask.objects.filter(
        achievementmember__isnull=True
    )

    new_members = []
    for task in missing_tasks:
        achievementmember = AchievementMember()
        achievementmember.member = member
        achievementmember.achievement_task = task
        new_members.append(achievementmember)

    if new_members:
        AchievementMember.objects.bulk_create(new_members)


def _filter_sales(achievement_members: list[AchievementMember], member:Member) -> dict:

    # Prefetch sales for all members in a single query
    sales_qs = Sale.objects.filter(
        timestamp__gte=min(am.begin_at for am in achievement_members) - timedelta(seconds=1),
        member=member
    ).select_related('product').prefetch_related('product__categories')

    task_to_sales = {}
    for am in achievement_members:
        task = am.achievement_task
        relevant_sales = sales_qs.filter(
            timestamp__gte=am.begin_at - timedelta(seconds=1)
        )

        if task.product:
            relevant_sales = relevant_sales.filter(product=task.product)

        if task.category:
            relevant_sales = relevant_sales.filter(product__categories=task.category)

        task_to_sales[task] = relevant_sales

    return task_to_sales


def _filter_achievement_tasks(product, categories, now):

    achievements_with_constraints = Achievement.objects.prefetch_related('achievementconstraint_set')

    # Step 1: Get all active achievements
    active_achievements = [
        a for a in achievements_with_constraints
        if _is_achievement_active(a, now)
    ]
    active_ids = [a.id for a in active_achievements]

    if not active_ids:
        return AchievementTask.objects.none()

    # Step 2: Get only tasks for active achievements
    tasks = AchievementTask.objects.filter(achievement_id__in=active_ids)

    # Step 3: Build your filter
    category_or_product = Q()
    if product:
        category_or_product |= Q(product_id=product)

    for category in categories:
        category_or_product |= Q(category_id=category)

    matching_filter = Q(task_type="any") | Q(task_type="balance") | (Q(task_type="default") & category_or_product)

    # Step 4: Find achievement IDs with at least one matching task
    matching_achievement_ids = set(
        tasks.filter(matching_filter).values_list("achievement_id", flat=True)
    )

    # Step 5: Return all tasks for those achievements
    return AchievementTask.objects.filter(achievement_id__in=matching_achievement_ids)


def _is_achievement_active(achievement: Achievement, now: datetime) -> bool:
    if achievement.globally_active_from and now < achievement.globally_active_from:
        return False
    if achievement.globally_active_until and now > achievement.globally_active_until:
        return False
    
    constraints = achievement.achievementconstraint_set.all()
    if not constraints:
        return True  # No constraints at all
    
    for c in constraints.all():
        if c.month_start and now.month < c.month_start:
            continue
        if c.month_end and now.month > c.month_end:
            continue
        if c.day_start and now.day < c.day_start:
            continue
        if c.day_end and now.day > c.day_end:
            continue
        if c.time_start and now.time() < c.time_start:
            continue
        if c.time_end and now.time() > c.time_end:
            continue
        if c.weekday and now.strftime("%a").lower()[:3] != c.weekday:
            continue
        return True  # passes one valid constraint block

    return False