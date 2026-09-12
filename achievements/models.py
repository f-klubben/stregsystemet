from datetime import datetime
from typing import List, Dict, Tuple

import pytz
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Count, Sum, QuerySet
from django.db.models import Prefetch
from stregsystem.models import (
    Product,
    Category,
    Sale,
    Member,
    BaseModel,
)
from django.conf import settings


class AchievementTask(BaseModel):
    notes = models.CharField(max_length=200, blank=True)

    TASK_TYPES = [
        # Specific item types
        ("product", "Specific Product"),
        ("category", "Product Category"),
        # Broad purchase-based task
        ("any_purchase", "Any Purchase"),
        # Content-based goals
        ("alcohol_content", "Alcohol Content"),
        ("caffeine_content", "Caffeine Content"),
        # Financial-based goals
        ("used_funds", "Used Funds"),
        ("remaining_funds", "Remaining Funds"),
    ]
    task_type = models.CharField(
        max_length=50,
        choices=TASK_TYPES,
        null=False,
        blank=False,
    )

    product: models.ForeignKey[Product | None, Product | None] = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Only has to be set, if 'Specific Product' was chosen as the Task Type.",
    )

    category: models.ForeignKey[Category | None, Category | None] = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Only has to be set, if 'Product Category' was chosen as the Task Type.",
    )

    goal_value = models.IntegerField(help_text="E.g. 300 = 3.00ml or mg. For funds: 500 = 5.00 kr.")

    def is_relevant(self, product: Product, category_ids: List[int] | None = None) -> bool:
        """
        Returns True if the task is relevant for the given product.
        Pass pre-fetched category_ids to avoid extra DB queries in loops.
        """

        if self.task_type in ["any_purchase", "used_funds", "remaining_funds"]:
            return True
        if self.task_type == "product":
            if not self.product:
                raise ValueError("Product must be set for product-based tasks.")
            return self.product.pk == product.pk
        if self.task_type == "category":
            if not self.category:
                raise ValueError("Category must be set for category-based tasks.")
            ids = category_ids if category_ids is not None else list(product.categories.values_list('id', flat=True))
            return self.category.pk in ids
        if self.task_type == "alcohol_content" and getattr(product, 'alcohol_content_ml', 0) > 0:
            return True
        if self.task_type == "caffeine_content" and getattr(product, 'caffeine_content_mg', 0) > 0:
            return True
        return False

    def is_task_completed(self, sales: QuerySet[Sale, Sale], member: Member) -> bool:
        """
        Determines if the task is completed based on the sales and member's attributes.
        """
        task_type = self.task_type
        used_funds = sales.aggregate(total=Sum('price'))['total'] or 0  # Sum of prices
        remaining_funds = member.balance
        alcohol_promille = member.calculate_alcohol_promille()
        caffeine = member.calculate_caffeine_in_body()

        if (
            task_type == "product" or task_type == "category" or task_type == "any_purchase"
        ) and sales.count() < self.goal_value:
            return False
        elif task_type == "alcohol_content" and alcohol_promille < (self.goal_value / 100):
            return False
        elif task_type == "caffeine_content" and caffeine < (self.goal_value / 100):
            return False
        elif task_type == "used_funds" and used_funds < self.goal_value:
            return False
        elif task_type == "remaining_funds" and remaining_funds < self.goal_value:
            return False

        return True

    def clean(self):
        super().clean()

        if not self.task_type:
            raise ValidationError("Task type must be selected.")

        if self.task_type == "product":
            if not self.product:
                raise ValidationError("Product must be set if task_type is 'product'.")
            if self.category:
                raise ValidationError("Category must not be set when task_type is 'product'.")
        elif self.task_type == "category":
            if not self.category:
                raise ValidationError("Category must be set if task_type is 'category'.")
            if self.product:
                raise ValidationError("Product must not be set when task_type is 'category'.")
        elif self.task_type in ("alcohol_content", "caffeine_content"):
            if self.product or self.category:
                raise ValidationError("Product and Category must not be set when target is alcohol or caffeine.")

        # Ensure goal_value is positive
        if self.goal_value <= 0:
            raise ValidationError("Goal value must be greater than 0.")

    def __str__(self):
        str_list = []

        if self.notes != "":
            return self.notes

        if self.task_type == "product" and self.product:
            str_list.append(f"Product: {self.product.name}")
        elif self.task_type == "category" and self.category:
            str_list.append(f"Category: {self.category.name}")
        elif self.task_type == "any_purchase":
            str_list.append("Any Purchase")
        elif self.task_type == "alcohol_content":
            str_list.append(f"Alcohol Content ≥ {self.goal_value / 100:.2f} ml")
        elif self.task_type == "caffeine_content":
            str_list.append(f"Caffeine Content ≥ {self.goal_value / 100:.2f} mg")
        elif self.task_type == "used_funds":
            str_list.append(f"Used Funds ≥ {self.goal_value / 100:.2f} kr")
        elif self.task_type == "remaining_funds":
            str_list.append(f"Remaining Funds ≥ {self.goal_value / 100:.2f} kr")

        return " | ".join(str_list) + f" - Goal: {self.goal_value}"


class AchievementConstraint(BaseModel):
    notes = models.CharField(max_length=200, blank=True)

    MONTHS = [
        (1, "January"),
        (2, "February"),
        (3, "March"),
        (4, "April"),
        (5, "May"),
        (6, "June"),
        (7, "July"),
        (8, "August"),
        (9, "September"),
        (10, "October"),
        (11, "November"),
        (12, "December"),
    ]

    month_start = models.IntegerField(
        choices=MONTHS,
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text="If not set, other constraints to no specific months. (requires Month End).",
    )

    month_end = models.IntegerField(
        choices=MONTHS,
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text="If not set, other constraints to no specific months. (requires Month Start).",
    )

    day_start = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text="If not set, constraints apply to no specific days. (requires Day End).",
    )

    day_end = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text="If not set, other constraints apply no specfic days. (requires Day Start).",
    )

    time_start = models.TimeField(
        null=True,
        blank=True,
        help_text="If not set, other constraints apply no specfic time range. (requires Time End).",
    )

    time_end = models.TimeField(
        null=True,
        blank=True,
        help_text="If not set, other constraints apply no specfic time range. (requires Time Start).",
    )

    WEEK_DAYS = [
        (0, "Monday"),
        (1, "Tuesday"),
        (2, "Wednesday"),
        (3, "Thursday"),
        (4, "Friday"),
        (5, "Saturday"),
        (6, "Sunday"),
    ]

    weekday = models.IntegerField(
        choices=WEEK_DAYS, null=True, blank=True, help_text="If not set, other constraints apply no specfic weekday."
    )

    def is_active(self, now: datetime) -> bool:
        return (
            (not self.month_start or now.month >= self.month_start)
            and (not self.month_end or now.month <= self.month_end)
            and (not self.day_start or now.day >= self.day_start)
            and (not self.day_end or now.day <= self.day_end)
            and (not self.time_start or now.time() >= self.time_start)
            and (not self.time_end or now.time() <= self.time_end)
            and (self.weekday is None or now.weekday() == self.weekday)
        )

    def clean(self):
        errors = {}

        # Helper to validate pairs
        def validate_pair(start, end, wrap_around=False):
            start_val = getattr(self, start)
            end_val = getattr(self, end)

            if start_val is not None and end_val is None:
                errors[end] = f"{start} must be set if {end} is set."
            elif end_val is not None and start_val is None:
                errors[start] = f"{end} must be set if {start} is set."
            elif start_val is not None and end_val is not None and not wrap_around:
                if start_val > end_val:
                    errors[start] = f"{start} must be less than or equal to {end}."

        validate_pair('month_start', 'month_end')
        validate_pair('day_start', 'day_end')
        validate_pair('time_start', 'time_end', wrap_around=True)

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        str_list = []

        if self.notes != "":
            return self.notes

        if self.month_start and self.month_end:
            str_list.append(f"Months: {self.month_start}-{self.month_end}")
        if self.day_start and self.day_end:
            str_list.append(f"Days: {self.day_start}-{self.day_end}")
        if self.time_start and self.time_end:
            str_list.append(f"Time: {self.time_start.strftime('%H:%M')}–{self.time_end.strftime('%H:%M')}")
        if self.weekday is not None:
            weekday_dict = dict(self.WEEK_DAYS)
            str_list.append(f"Weekday: {weekday_dict[int(self.weekday)]}")

        return ", ".join(str_list)


class Achievement(BaseModel):
    title = models.CharField(max_length=50)
    description = models.CharField(max_length=100)
    icon = models.ImageField(upload_to="stregsystem/achievement")

    active_from = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Start datetime for tracking. Conflicts with 'Active Duration'. Leave both blank for all-time history.",
    )

    active_duration = models.DurationField(
        null=True,
        blank=True,
        help_text="Time window for tracking. Conflicts with 'Active From'. Leave both blank for all-time history.",
    )

    constraints = models.ManyToManyField(
        AchievementConstraint,
        blank=True,
        related_name='achievements',
        help_text="Optional time-based constraints for this achievement.",
    )

    tasks = models.ManyToManyField(
        AchievementTask,
        related_name='achievements',
        help_text="Tasks that must be completed to earn this achievement.",
    )

    completed_count: int  # added by annotation

    def is_active(self, now: datetime) -> bool:
        constraints = self.constraints.all()

        if not constraints.exists():
            return True

        return all(c.is_active(now) for c in constraints)  # All constraints needs to be active

    def is_relevant_for_purchase(self, product: Product, category_ids: List[int] | None = None) -> bool:
        tasks = self.tasks.all()
        return any(t.is_relevant(product, category_ids) for t in tasks)

    def clean(self):
        super().clean()
        if self.active_from and self.active_duration:
            raise ValidationError("Only one of 'Active From' or 'Active Duration' can be set, or neither.")

    def __str__(self):
        str_list = [f"{self.title} - {self.description}"]

        if self.active_from:
            str_list.append(f"Starts: {self.active_from.strftime('%Y-%m-%d')}")
        if self.active_duration:
            str_list.append(f"Duration: {self.active_duration}")

        return " | ".join(str_list)


class AchievementComplete(BaseModel):  # A members progress on a task
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta(BaseModel.Meta):
        unique_together = ("member", "achievement")

    def __str__(self):
        return f"{self.member.username} ({self.achievement.title})"


def get_new_achievements(member: Member, product: Product, amount: int = 1) -> List[Achievement]:
    """
    Gets newly acquired achievements after having bought something
    (This function assumes that a Sale was JUST made)
    """

    now = datetime.now(tz=pytz.timezone(settings.TIME_ZONE))

    # Step 1: Get IDs of achievements already completed by the member
    finished_achievements = AchievementComplete.objects.filter(member=member)

    # Step 2: Filter out achievements already completed
    finished_achievement_ids = finished_achievements.values_list('achievement_id', flat=True)
    in_progress_achievements = Achievement.objects.exclude(id__in=finished_achievement_ids)

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
    total_members = Member.objects.filter(achievementcomplete__isnull=False).distinct().count()

    if total_members == 0:
        return []

    # For each of those achievements, calculate how many members have completed it
    achievements_with_counts = Achievement.objects.annotate(
        completed_count=Count('achievementcomplete__member', distinct=True)
    ).filter(achievementcomplete__member=member)

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

    output is a float between 0.0 and 100.0 (2 decimal places)
    """
    # Build leaderboard with total achievement counts
    leaderboard = (
        AchievementComplete.objects.all()
        .values('member')
        .annotate(total=Count('id'))
        .order_by('-total', 'member')  # tie-break deterministically
    )

    if not leaderboard:
        return 100.0

    # Assign ranks with dense ranking
    ranks = {}
    current_rank = 1
    rank = 1
    last_total = None

    for entry in leaderboard:
        member_id = entry['member']
        total = entry['total']

        if total != last_total:
            rank = current_rank

        ranks[member_id] = rank
        last_total = total
        current_rank += 1

    if member.pk not in ranks:
        return 100.0  # Member has no achievements

    member_rank = ranks[member.pk]
    total_ranks = len(ranks)
    result = member_rank / total_ranks
    return round(result * 100, 2)


def _find_completed_achievements(
    related_achievements: List[Achievement], member: Member, now: datetime
) -> List[Achievement]:

    # Filter member's sales to match relevant achievement tasks
    task_to_sales = _filter_relevant_sales(related_achievements, member, now)

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


def _filter_relevant_sales(
    achievements: List[Achievement], member: Member, now: datetime
) -> Dict[AchievementTask, QuerySet[Sale, Sale]]:
    # Start with all sales for this member, select related to reduce hits
    member_sales = Sale.objects.filter(member=member).select_related('product').prefetch_related('product__categories')
    task_to_sales: Dict[AchievementTask, QuerySet[Sale, Sale]] = {}

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
                        timestamp__month__gte=constraint.month_start, timestamp__month__lte=constraint.month_end
                    )
                if constraint.day_start and constraint.day_end:
                    relevant_sales = relevant_sales.filter(
                        timestamp__day__gte=constraint.day_start, timestamp__day__lte=constraint.day_end
                    )
                if constraint.time_start and constraint.time_end:
                    relevant_sales = relevant_sales.filter(
                        timestamp__time__gte=constraint.time_start, timestamp__time__lte=constraint.time_end
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
    product: Product, constraints: QuerySet[Achievement], now: datetime
) -> List[Achievement]:

    # Prefetch constraints and tasks with related product and category data
    achievements_qs = constraints.prefetch_related(
        Prefetch('constraints'),
        Prefetch('tasks', queryset=AchievementTask.objects.select_related('product', 'category')),
    )

    # List to store filtered achievements
    relevant_achievements: List[Achievement] = []

    # Iterate through achievements and filter based on activity and relevance
    for achievement in achievements_qs:
        # Check if the achievement is active and relevant to the purchased product
        if achievement.is_active(now) and achievement.is_relevant_for_purchase(product):
            relevant_achievements.append(achievement)

    return relevant_achievements
