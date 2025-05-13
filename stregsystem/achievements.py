from django.db.models import Q, Count, Sum, QuerySet
from django.db import models
from collections import defaultdict

from typing import List, Dict
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


def get_new_achievements(member: Member, product: Product, amount: int = 1) -> List[Achievement]:
    """
    Gets newly acquired achievements after having bought something
    (This function assumes that a Sale was JUST made)
    """

    categories = list(product.categories.values_list('id', flat=True))
    now = datetime.now(tz=pytz.timezone("Europe/Copenhagen"))

    # Step 1: Get IDs of achievements already completed by the member
    completed_achievements = AchievementComplete.objects.filter(member=member)

    # Step 2: Filter out achievements already completed
    completed_achievement_ids = completed_achievements.values_list('achievement_id', flat=True)
    in_progress_achievements = Achievement.objects.exclude(id__in=completed_achievement_ids)

    # Step 3: Find tasks from the remaining achievements that are relevant to the purchase
    related_achievement_tasks: List[AchievementTask] = _filter_achievement_tasks(
        product, categories, in_progress_achievements, now
    )

    # Step 4: Determine which of the related tasks now meet their criteria
    completed_achievements: List[Achievement] = _find_completed_achievements(related_achievement_tasks, member, now)

    # Step 5: Convert into a dictionary for easy variable retrieval
    return completed_achievements


def get_acquired_achievements(member: Member) -> QuerySet[Achievement]:
    """Gets all acquired achievements for a member"""
    completed_achievements = Achievement.objects.filter(achievementcomplete__member=member).distinct()

    return completed_achievements


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
    Example: 0.1 means top 10%.
    """
    # Count number of achievements completed per member
    leaderboard = (
        AchievementComplete.objects.filter(completed_at__isnull=False)
        .values('member')
        .annotate(total=Count('id'))  # Count of achievements per user
        .order_by('-total')  # Rank by total descending
    )

    total_members = leaderboard.count()
    if total_members == 0:
        return 1.0  # No data, treat user as lowest rank

    # Find the current user's index (rank)
    for index, entry in enumerate(leaderboard):
        if entry['member'] == member.id:
            position = index + 1  # Convert to 1-based rank
            break
    else:
        return 1.0  # User has no achievements

    return position / total_members  # Normalize to percentage


def _find_completed_achievements(
    related_achievement_tasks: List[AchievementTask], member: Member, now: datetime
) -> List[Achievement]:

    # Filter member's sales to match relevant achievement tasks
    task_to_sales: Dict[int, QuerySet[Sale]] = _filter_sales(related_achievement_tasks, member, now)

    # Group tasks by achievement for evaluation
    achievement_groups: Dict[int, List[AchievementTask]] = defaultdict(list)
    for at in related_achievement_tasks:
        achievement_groups[at.achievement_id].append(at)

    completed_achievements: List[Achievement] = []
    new_completions: List[AchievementComplete] = []

    for group in achievement_groups.values():
        is_completed: bool = True

        for at in group:

            task_type = at.task_type
            sales = task_to_sales[at.id]
            used_funds = sales.aggregate(total=Sum('price'))['total']  # Sum of prices
            remaining_funds = member.balance
            alcohol_promille = member.calculate_alcohol_promille()
            caffeine = member.calculate_caffeine_in_body()

            # Evaluate whether the specific task is completed based on type
            if task_type == "default" or task_type == "any":

                if at.alcohol_content and alcohol_promille < (at.goal_count / 100):
                    is_completed = False

                elif at.caffeine_content and caffeine < (at.goal_count / 100):
                    is_completed = False

                elif (not at.alcohol_content and not at.caffeine_content) and sales.count() < at.goal_count:
                    is_completed = False

            elif task_type == "used_funds" and used_funds < at.goal_count:
                is_completed = False
            elif task_type == "remaining_funds" and remaining_funds < at.goal_count:
                is_completed = False

        if is_completed:
            achievement = group[0].achievement
            completed_achievements.append(achievement)
            new_completions.append(AchievementComplete(member=member, achievement=achievement))

    if new_completions:
        AchievementComplete.objects.bulk_create(new_completions)

    return completed_achievements


def _filter_sales(achievement_tasks: List[AchievementTask], member: Member, now: datetime) -> Dict[int, QuerySet[int]]:

    # Prefetch product and categories to reduce DB hits later
    sales_qs = Sale.objects.filter(member=member).select_related('product').prefetch_related('product__categories')
    task_to_sales: Dict[int, QuerySet[int]] = {}

    for at in achievement_tasks:
        achievement = at.achievement
        relevant_sales = sales_qs

        # Determine the valid time window for the sales
        if achievement.duration:
            begin_time = now - achievement.duration
        elif achievement.begin_at:
            begin_time = achievement.begin_at
        else:
            begin_time = None

        if begin_time:
            relevant_sales = relevant_sales.filter(timestamp__gte=begin_time)

        # Additional filtering based on achievement constraints
        constraints = achievement.achievementconstraint_set.all()
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
            if constraint.weekday:
                weekday_map = {
                    'mon': 0, 'tue': 1, 'wed': 2,
                    'thu': 3, 'fri': 4, 'sat': 5, 'sun': 6
                }
                weekday_int = weekday_map.get(constraint.weekday[:3].lower(), None)
                if weekday_int is not None:
                    relevant_sales = relevant_sales.filter(timestamp__week_day=((weekday_int + 2) % 7 + 1))


        # Filter for specific product if defined
        if at.product:
            relevant_sales = relevant_sales.filter(product=at.product)

        # Filter for category match
        if at.category:
            relevant_sales = relevant_sales.filter(product__categories=at.category)

        # Use only sale IDs to reduce payload
        task_to_sales[at.id] = relevant_sales.values_list('id', flat=True)

    return task_to_sales


def _filter_achievement_tasks(
    product: Product, categories: List[int], in_progress_achievements: QuerySet[Achievement], now: datetime
) -> List[AchievementTask]:

    # Load constraint relations in advance to avoid N+1 queries
    achievements_with_constraints = in_progress_achievements.prefetch_related('achievementconstraint_set')

    # Step 1: Filter achievements that are currently "active"
    active_achievements = [a for a in achievements_with_constraints if _is_achievement_active(a, now)]
    active_ids = [a.id for a in active_achievements]

    if not active_ids:
        return AchievementTask.objects.none()  # Return empty queryset early

    # Step 2: Get all tasks from the active achievements
    tasks = AchievementTask.objects.filter(achievement_id__in=active_ids)

    # Step 3: Build filter matching product or category depending on task type
    category_or_product = Q()
    if product:
        category_or_product |= Q(product_id=product)

    for category in categories:
        category_or_product |= Q(category_id=category)

    # Step 3.1: Add alcohol/caffeine matching if product has it
    alcohol_or_caffeine_filter = Q()
    if product:

        if product.alcohol_content_ml and product.alcohol_content_ml > 0:
            alcohol_or_caffeine_filter |= Q(alcohol_content=True)

        if product.caffeine_content_mg and product.caffeine_content_mg > 0:
            alcohol_or_caffeine_filter |= Q(caffeine_content=True)

    # Step 4: Combine with supported task types
    matching_filter = (
        Q(task_type="any")
        | Q(task_type="used_funds")
        | Q(task_type="remaining_funds")
        | (Q(task_type="default") & (category_or_product | alcohol_or_caffeine_filter))
    )

    # Step 5: Only include achievements with at least one matching task
    matching_achievement_ids = set(tasks.filter(matching_filter).values_list("achievement_id", flat=True))

    # Step 6: Return all tasks from matching achievements
    return list(
        AchievementTask.objects.filter(achievement_id__in=matching_achievement_ids).select_related(
            'achievement', 'product', 'category'
        )
    )


def _is_achievement_active(achievement: Achievement, now: datetime) -> bool:
    constraints = achievement.achievementconstraint_set.all()
    if not constraints:
        return True  # No constraint means always active

    for c in constraints.all():
        # All checks must *fail* to continue; pass means active
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
        return True  # At least one constraint matches

    return False  # All constraints failed
