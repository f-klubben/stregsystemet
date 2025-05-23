from django.db.models import Q, Count, Sum, QuerySet
from django.db import models
from collections import defaultdict
from django.db.models import Prefetch

from typing import List, Dict, Tuple
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
    AchievementConstraint
)


def get_new_achievements(member: Member, product: Product, amount: int = 1) -> List[Achievement]:
    """
    Gets newly acquired achievements after having bought something
    (This function assumes that a Sale was JUST made)
    """

    now = datetime.now(tz=pytz.timezone("Europe/Copenhagen"))

    # Step 1: Get IDs of achievements already completed by the member
    completed_achievements = AchievementComplete.objects.filter(member=member)

    # Step 2: Filter out achievements already completed
    completed_achievement_ids = completed_achievements.values_list('achievement_id', flat=True)
    in_progress_achievements = Achievement.objects.exclude(id__in=completed_achievement_ids)

    # Step 3: Find achievements that are relevant to the purchase
    related_achievements: List[Achievement] = _filter_active_relevant_achievements(
        product, in_progress_achievements, now
    )

    # Step 4: Determine which of the related tasks now meet their criteria
    completed_achievements: List[Achievement] = _find_completed_achievements(related_achievements, member, now)

    # Step 5: Convert into a dictionary for easy variable retrieval
    return completed_achievements


def get_acquired_achievements_with_rarity(member: Member) -> List[Tuple[Achievement, float]]:
    """
    Gets all acquired achievements for a member along with their rarity.
    Rarity is defined as the percentage of members who have acquired the achievement.
    """

    # Get the total number of members who have completed any achievement
    total_members = Member.objects.filter(
        achievementcomplete__isnull=False
    ).distinct().count()

    if total_members == 0:
        return []

    # For each of those achievements, calculate how many members have completed it
    achievements_with_counts = Achievement.objects.annotate(
        completed_count=Count('achievementcomplete__member', distinct=True)
    ).filter(
        achievementcomplete__member=member
    )

    # Compute rarity as percentage
    result = [
        (achievement, round((achievement.completed_count / total_members) * 100, 2))
        for achievement in achievements_with_counts
    ]

    return result


def get_missing_achievements(member: Member) -> QuerySet[Achievement]:
    """Gets all missing achievements for a member"""
    completed_achievements = AchievementComplete.objects.filter(member=member)
    completed_achievement_ids = completed_achievements.values_list('achievement_id', flat=True)
    missing_achievements = Achievement.objects.exclude(id__in=completed_achievement_ids)

    return missing_achievements


def get_user_leaderboard_position(member: Member) -> float:
    """
    Returns the top percentage that the member is in
    based on number of completed achievements among all users.
    Users with the same total share the same rank.
    """
    # Build leaderboard with total achievement counts
    leaderboard = (
        AchievementComplete.objects.all()
        .values('member')
        .annotate(total=Count('id'))
        .order_by('-total', 'member')  # tie-break deterministically
    )

    if not leaderboard:
        return 1.0

    # Assign ranks with dense ranking
    ranks = {}
    current_rank = 1
    last_total = None

    for entry in leaderboard:
        member_id = entry['member']
        total = entry['total']

        if total != last_total:
            rank = current_rank
        # if total == last_total, keep previous rank

        ranks[member_id] = rank
        last_total = total
        current_rank += 1

    if member.id not in ranks:
        return 1.0  # Member has no achievements

    member_rank = ranks[member.id]
    total_ranks = len(set(ranks.values()))  # total distinct rank positions

    return member_rank / total_ranks


def _find_completed_achievements(
    related_achievements: List[Achievement], member: Member, now: datetime
) -> List[Achievement]:

    # Filter member's sales to match relevant achievement tasks
    task_to_sales: Dict[AchievementTask, QuerySet[Sale]] = _filter_relevant_sales(related_achievements, member, now)

    completed_achievements: List[Achievement] = []
    new_completions: List[AchievementComplete] = []

    for achievement in related_achievements:
        tasks = achievement.tasks.all()

        if all(task.is_task_completed(task_to_sales[task], member) for task in tasks):
            completed_achievements.append(achievement)
            new_completions.append(AchievementComplete(member=member, achievement=achievement))

    if new_completions:
        AchievementComplete.objects.bulk_create(new_completions)

    return completed_achievements


def _filter_relevant_sales(achievements: List[Achievement], member: Member, now: datetime) -> Dict[AchievementTask, QuerySet[Sale]]:
    # Start with all sales for this member, select related to reduce hits
    member_sales = Sale.objects.filter(member=member).select_related('product').prefetch_related('product__categories')
    task_to_sales: Dict[int, QuerySet[int]] = {}

    for achievement in achievements:
        # Determine global time window
        if achievement.active_duration:
            cutoff_date = now - achievement.active_duration
        elif achievement.active_from:
            cutoff_date = achievement.active_from
        else:
            cutoff_date = None

        # Apply constraints
        constraints = achievement.constraints.all()
        tasks = achievement.tasks.all()

        for task in tasks:
            relevant_sales = member_sales

            # Apply global achievement time filter
            if cutoff_date:
                relevant_sales = relevant_sales.filter(timestamp__gte=cutoff_date)

            # Apply all time-based constraints
            for constraint in constraints:
                if constraint.month_start and constraint.month_end:
                    relevant_sales = relevant_sales.filter(
                        timestamp__month__gte=constraint.month_start,
                        timestamp__month__lte=constraint.month_end
                    )
                if constraint.day_start and constraint.day_end:
                    relevant_sales = relevant_sales.filter(
                        timestamp__day__gte=constraint.day_start,
                        timestamp__day__lte=constraint.day_end
                    )
                if constraint.time_start and constraint.time_end:
                    relevant_sales = relevant_sales.filter(
                        timestamp__time__gte=constraint.time_start,
                        timestamp__time__lte=constraint.time_end
                    )
                if constraint.weekday is not None:
                    # Django uses Sunday=1 to Saturday=7
                    django_weekday = ((constraint.weekday + 1) % 7) + 1
                    relevant_sales = relevant_sales.filter(timestamp__week_day=django_weekday)

            # Filter by product/category if defined on the task
            if task.task_type == "product" and task.product:
                relevant_sales = relevant_sales.filter(product=task.product)
            elif task.task_type == "category" and task.category:
                relevant_sales = relevant_sales.filter(product__categories=task.category)
            # For other task types, additional logic may be added as needed

            task_to_sales[task] = relevant_sales

    return task_to_sales


def _filter_active_relevant_achievements(
    product: Product,
    constraints: QuerySet[Achievement],
    now: datetime
) -> List[Achievement]:

    # Prefetch constraints and tasks with related product and category data
    achievements_qs = constraints.prefetch_related(
        Prefetch('constraints'),
        Prefetch('tasks', queryset=AchievementTask.objects.select_related('product', 'category'))
    )

    # List to store filtered achievements
    relevant_achievements: List[Achievement] = []

    # Iterate through achievements and filter based on activity and relevance
    for achievement in achievements_qs:
        # Check if the achievement is active and relevant to the purchased product
        if achievement.is_active(now) and achievement.is_relevant_for_purchase(product):
            relevant_achievements.append(achievement)

    return relevant_achievements