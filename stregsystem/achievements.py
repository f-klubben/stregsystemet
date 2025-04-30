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
    AchievementComplete,
    AchievementTask,
)

def get_new_achievements(member:Member, product:Product, amount=1): 
    """Gets newly acquired achievements after having bought something"""

    categories = product.categories.values_list('id', flat=True)
    now = datetime.now(tz=pytz.timezone("Europe/Copenhagen"))

    # Step 1: Get IDs of completed achievements for a member
    completed_achievements = AchievementComplete.objects.filter(member=member)

    # Step 2: Filter out all achievements that are completed
    completed_achievement_ids = completed_achievements.values_list('achievement_id', flat=True)
    in_progress_achievements = Achievement.objects.exclude(id__in=completed_achievement_ids)

    # Step 3: Query for all related achievement tasks out of the in progress achievements
    related_achievement_tasks = _filter_achievement_tasks(product, categories, in_progress_achievements, now)

    # Step 4: Check if any of the achievement tasks can be considered "completed". If so, add an entry in AchievementComplete
    completed_achievements = _find_completed_achievements(related_achievement_tasks, member)

    # Step 5: Convert into a dictionary for easy variable retrieval
    return completed_achievements


def get_acquired_achievements(member:Member):
    """Gets all acquired achievements for a member"""
    achievement_completed = AchievementComplete.objects.filter(
        member=member
    ).select_related("achievement")

    return achievement_completed.achievement


def get_missing_achievements(member:Member):
    """Gets all missing achievements for a member"""
    completed_achievements = AchievementComplete.objects.filter(member=member)
    completed_achievement_ids = completed_achievements.values_list('achievement_id', flat=True)
    missing_achievements = Achievement.objects.exclude(id__in=completed_achievement_ids)
    
    return missing_achievements


def get_user_leaderboard_position(member: Member):
    """
    Returns the top percentage that the member is in 
    based on number of completed achievements among all users.
    Example: 0.1 means top 10%.
    """
    # Count completed achievements per user
    leaderboard = (
        AchievementComplete.objects
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


def _find_completed_achievements(related_achievement_tasks, member):
            
    task_to_sales = _filter_sales(related_achievement_tasks, member)

    achievement_groups = defaultdict(list)
    for at in related_achievement_tasks:
        achievement_groups[at.achievement_id].append(at)

    completed_achievements = []
    new_completions = []
    for group in achievement_groups.values():
        if all(task_to_sales[at.id].count() >= at.goal_count for at in group):
            achievement = group[0].achievement  # All `at`s in group share the same achievement
            completed_achievements.append(achievement)
            for at in group:
                new_completions.append(
                    AchievementComplete(member=member, achievement=achievement)
                )

    if new_completions:
        AchievementComplete.objects.bulk_create(new_completions)

    return completed_achievements

def _filter_sales(achievement_tasks: list[AchievementTask], member: Member) -> dict:
    begin_ats = [at.achievement.begin_at for at in achievement_tasks if at.achievement.begin_at]
    
    sales_qs = Sale.objects.filter(member=member).select_related('product').prefetch_related('product__categories')

    if begin_ats:
        min_begin_at = min(begin_ats) - timedelta(seconds=1)
        sales_qs = sales_qs.filter(timestamp__gte=min_begin_at)

    task_to_sales = {}
    for at in achievement_tasks:
        relevant_sales = sales_qs

        if at.achievement.begin_at:
            relevant_sales = relevant_sales.filter(timestamp__gte=at.achievement.begin_at - timedelta(seconds=1))

        if at.product:
            relevant_sales = relevant_sales.filter(product=at.product)

        if at.category:
            relevant_sales = relevant_sales.filter(product__categories=at.category)

        task_to_sales[at.id] = relevant_sales.values_list('id', flat=True)

    return task_to_sales


def _filter_achievement_tasks(product, categories, in_progress_achievements, now):

    achievements_with_constraints = in_progress_achievements.prefetch_related('achievementconstraint_set')

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
    return AchievementTask.objects.filter(achievement_id__in=matching_achievement_ids
                                          ).select_related('achievement', 'product', 'category')


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