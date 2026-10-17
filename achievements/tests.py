import pytz
from django.core.exceptions import ValidationError
from achievements.models import (
    get_new_achievements,
    get_acquired_achievements_with_rarity,
    get_missing_achievements,
    get_user_leaderboard_position,
)
from achievements.models import AchievementConstraint, AchievementTask, Achievement, AchievementComplete
from django.test import TestCase
from freezegun import freeze_time
from stregsystem.models import Member, Category, Product, Sale
import datetime
from django.db.models import QuerySet

# category -> ((rank, total_buyers), per_uni_day, my_count), as returned by get_member_rankings
Rankings = dict[Category, tuple[tuple[int, int], str, int]]
CPH_TZ = pytz.timezone("Europe/Copenhagen")


class AchievementTaskTests(TestCase):
    def setUp(self):
        self.category_beer = Category.objects.create(name="Beer Category")
        self.category_soda = Category.objects.create(name="Soda Category")
        self.product_beer = Product.objects.create(name="Beer", price=10, alcohol_content_ml=500, active=True)
        self.product_beer.categories.add(self.category_beer)
        self.product_soda = Product.objects.create(name="Soda", price=5, caffeine_content_mg=100, active=True)
        self.product_soda.categories.add(self.category_soda)

        self.cph_tz = pytz.timezone("Europe/Copenhagen")

    def test_is_relevant_product_task(self):
        task = AchievementTask.objects.create(task_type="product", product=self.product_beer, goal_value=1)

        self.assertTrue(task.is_relevant([self.product_beer]))
        self.assertFalse(task.is_relevant([self.product_soda]))

    def test_is_relevant_category_task(self):
        task = AchievementTask.objects.create(task_type="category", category=self.category_beer, goal_value=1)

        self.assertTrue(task.is_relevant([self.product_beer]))
        self.assertFalse(task.is_relevant([self.product_soda]))

    def test_is_relevant_any_purchase_task(self):
        task = AchievementTask.objects.create(task_type="any_purchase", goal_value=1)

        self.assertTrue(task.is_relevant([self.product_beer]))
        self.assertTrue(task.is_relevant([self.product_soda]))

    def test_is_relevant_alcohol_content_task(self):
        task = AchievementTask.objects.create(task_type="alcohol_content", goal_value=100)

        self.assertTrue(task.is_relevant([self.product_beer]))
        self.assertFalse(task.is_relevant([self.product_soda]))

    def test_is_relevant_caffeine_content_task(self):
        task = AchievementTask.objects.create(task_type="caffeine_content", goal_value=100)

        self.assertFalse(task.is_relevant([self.product_beer]))
        self.assertTrue(task.is_relevant([self.product_soda]))

    def test_is_relevant_used_funds_task(self):
        task = AchievementTask.objects.create(task_type="used_funds", goal_value=100)

        # used_funds and remaining_funds tasks are always relevant
        self.assertTrue(task.is_relevant([self.product_beer]))
        self.assertTrue(task.is_relevant([self.product_soda]))

    def test_is_relevant_remaining_funds_task(self):
        task = AchievementTask.objects.create(task_type="remaining_funds", goal_value=100)

        # used_funds and remaining_funds tasks are always relevant
        self.assertTrue(task.is_relevant([self.product_beer]))
        self.assertTrue(task.is_relevant([self.product_soda]))

    def test_is_task_completed_product_task(self):
        member = Member.objects.create(username="testuser", balance=100)
        task = AchievementTask.objects.create(task_type="product", product=self.product_beer, goal_value=2)

        # Create 2 sales
        Sale.objects.create(member=member, product=self.product_beer, price=10)
        Sale.objects.create(member=member, product=self.product_beer, price=10)

        sales = Sale.objects.filter(member=member, product=self.product_beer)
        self.assertTrue(task.is_task_completed(sales, member, {}, {}))

    def test_is_task_completed_category_task(self):
        member = Member.objects.create(username="testuser", balance=100)
        task = AchievementTask.objects.create(task_type="category", category=self.category_beer, goal_value=1)

        # Create 1 sale in beer category
        Sale.objects.create(member=member, product=self.product_beer, price=10)

        sales = Sale.objects.filter(member=member, product__categories=self.category_beer)
        self.assertTrue(task.is_task_completed(sales, member, {}, {}))

    def test_is_task_completed_alcohol_content_task(self):
        member = Member.objects.create(username="testuser", balance=100)
        task = AchievementTask.objects.create(task_type="alcohol_content", goal_value=500)  # 5.00 ml

        # Create sale with beer (500 ml alcohol)
        Sale.objects.create(member=member, product=self.product_beer, price=10)

        sales = Sale.objects.filter(member=member)
        self.assertTrue(task.is_task_completed(sales, member, {}, {}))

    def test_is_task_completed_used_funds_task(self):
        member = Member.objects.create(username="testuser", balance=100)
        task = AchievementTask.objects.create(task_type="used_funds", goal_value=50)  # 50.00 kr

        # Create sales totaling 60 kr
        Sale.objects.create(member=member, product=self.product_beer, price=30)
        Sale.objects.create(member=member, product=self.product_beer, price=30)

        sales = Sale.objects.filter(member=member)
        self.assertTrue(task.is_task_completed(sales, member, {}, {}))

    def test_is_task_completed_remaining_funds_task(self):
        member = Member.objects.create(username="testuser", balance=100)
        task = AchievementTask.objects.create(task_type="remaining_funds", goal_value=50)  # 50.00 kr

        # Create sale that leaves member with 70 kr (above threshold)
        Sale.objects.create(member=member, product=self.product_beer, price=30)

        sales = Sale.objects.filter(member=member)
        self.assertTrue(task.is_task_completed(sales, member, {}, {}))

    def test_task_validation(self):
        # Test product task validation
        with self.assertRaises(ValidationError):
            task = AchievementTask(task_type="product", goal_value=1)
            task.full_clean()

        # Test category task validation
        with self.assertRaises(ValidationError):
            task = AchievementTask(task_type="category", goal_value=1)
            task.full_clean()

        # Test goal value validation
        with self.assertRaises(ValidationError):
            task = AchievementTask(task_type="any_purchase", goal_value=0)
            task.full_clean()


class AchievementConstraintTests(TestCase):
    def setUp(self):
        self.cph_tz = pytz.timezone("Europe/Copenhagen")

    def test_is_active_month_constraint(self):
        constraint = AchievementConstraint.objects.create(month_start=5, month_end=8)

        # Test within range
        may_date = self.cph_tz.localize(datetime.datetime(2025, 5, 15))
        self.assertTrue(constraint.is_active(may_date))

        # Test outside range
        november_date = self.cph_tz.localize(datetime.datetime(2025, 11, 15))
        self.assertFalse(constraint.is_active(november_date))

    def test_is_active_day_constraint(self):
        constraint = AchievementConstraint.objects.create(day_start=10, day_end=20)

        # Test within range
        mid_month_date = self.cph_tz.localize(datetime.datetime(2025, 5, 15))
        self.assertTrue(constraint.is_active(mid_month_date))

        # Test outside range
        early_month_date = self.cph_tz.localize(datetime.datetime(2025, 5, 5))
        self.assertFalse(constraint.is_active(early_month_date))

    def test_is_active_time_constraint(self):
        constraint = AchievementConstraint.objects.create(
            time_start=datetime.time(12, 0), time_end=datetime.time(18, 0)
        )

        # Test within range
        afternoon_date = self.cph_tz.localize(datetime.datetime(2025, 5, 15, 14, 0))
        self.assertTrue(constraint.is_active(afternoon_date))

        # Test outside range
        evening_date = self.cph_tz.localize(datetime.datetime(2025, 5, 15, 20, 0))
        self.assertFalse(constraint.is_active(evening_date))

    def test_is_active_weekday_constraint(self):
        constraint = AchievementConstraint.objects.create(weekday=3)  # Thursday

        # Test correct weekday
        thursday_date = self.cph_tz.localize(datetime.datetime(2025, 5, 15))  # May 15, 2025 is Thursday
        self.assertTrue(constraint.is_active(thursday_date))

        # Test wrong weekday
        friday_date = self.cph_tz.localize(datetime.datetime(2025, 5, 16))  # May 16, 2025 is Friday
        self.assertFalse(constraint.is_active(friday_date))

    def test_constraint_validation(self):
        # Test month pair validation
        with self.assertRaises(ValidationError):
            constraint = AchievementConstraint(month_start=8, month_end=5)
            constraint.full_clean()

        # Test day pair validation
        with self.assertRaises(ValidationError):
            constraint = AchievementConstraint(day_start=20, day_end=10)
            constraint.full_clean()


class AchievementModelTests(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="testuser", balance=100)
        self.category = Category.objects.create(name="Test Category")
        self.product = Product.objects.create(name="Test Product", price=10, active=True)
        self.product.categories.add(self.category)

        self.task = AchievementTask.objects.create(task_type="product", product=self.product, goal_value=1)

        self.achievement = Achievement.objects.create(title="Test Achievement", description="Test Description")
        self.achievement.tasks.add(self.task)

        self.cph_tz = pytz.timezone("Europe/Copenhagen")

    def test_is_active_no_constraints(self):
        now = self.cph_tz.localize(datetime.datetime(2025, 5, 15))
        self.assertTrue(self.achievement.is_active(now))

    def test_is_active_with_constraints(self):
        constraint = AchievementConstraint.objects.create(month_start=5, month_end=8)
        self.achievement.constraints.add(constraint)

        # Test within constraint
        may_date = self.cph_tz.localize(datetime.datetime(2025, 5, 15))
        self.assertTrue(self.achievement.is_active(may_date))

        # Test outside constraint
        november_date = self.cph_tz.localize(datetime.datetime(2025, 11, 15))
        self.assertFalse(self.achievement.is_active(november_date))

    def test_is_relevant_for_purchase(self):
        self.assertTrue(self.achievement.is_relevant_for_purchase([self.product]))

        other_product = Product.objects.create(name="Other Product", price=5, active=True)
        self.assertFalse(self.achievement.is_relevant_for_purchase([other_product]))

    def test_achievement_validation(self):
        # Test conflicting active_from and active_duration
        with self.assertRaises(ValidationError):
            achievement = Achievement(
                title="Test",
                description="Test",
                active_from=self.cph_tz.localize(datetime.datetime(2025, 1, 1)),
                active_duration=datetime.timedelta(days=30),
            )
            achievement.full_clean()


class AchievementLogicTests(TestCase):
    def setUp(self):
        self.member1 = Member.objects.create(username="testuser1", balance=100)
        self.member2 = Member.objects.create(username="testuser2", balance=100)
        self.member3 = Member.objects.create(username="testuser3", balance=100)
        self.category_beer = Category.objects.create(name="Beer Category")
        self.product_beer = Product.objects.create(name="Beer", price=10, alcohol_content_ml=500, active=True)
        self.product_beer.categories.add(self.category_beer)

        self.task_beer_drinker = AchievementTask.objects.create(
            task_type="product",
            product=self.product_beer,
            goal_value=1,
        )

        self.achievement_beer_drinker = Achievement.objects.create(
            title="Beer Drinker",
            description="Drink a Beer",
        )

        self.achievement_beer_drinker.tasks.add(self.task_beer_drinker)

        self.task_better_beer_drinker = AchievementTask.objects.create(
            task_type="product",
            product=self.product_beer,
            goal_value=2,
        )

        self.achievement_better_beer_drinker = Achievement.objects.create(
            title="Better Beer Drinker",
            description="Drink two Beers",
        )

        self.achievement_better_beer_drinker.tasks.add(self.task_better_beer_drinker)

        self.cph_tz = pytz.timezone("Europe/Copenhagen")

        self.create_sale = lambda: {Sale.objects.create(member=self.member1, product=self.product_beer, price=10)}

        self.create_achievement_complete = lambda a, m=self.member1: {
            AchievementComplete.objects.create(member=m, achievement=a)
        }

    def test_get_new_achievements_returns_correct_achievement(self):
        self.create_sale()

        new_achievements = get_new_achievements(self.member1, [self.product_beer])
        self.assertIn(self.achievement_beer_drinker, new_achievements)
        self.assertNotIn(self.achievement_better_beer_drinker, new_achievements)

    def test_get_new_achievements_constraints(self):
        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 5, 12, 12, 1))):
            self.create_sale()

        constraint = AchievementConstraint.objects.create(
            month_start=5,  # Only May
            month_end=5,
            day_start=12,
            day_end=13,
            time_start=datetime.time(12, 00),
            time_end=datetime.time(13, 00),
        )

        self.achievement_beer_drinker.constraints.add(constraint)

        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 5, 13, 12, 50, 0))):
            new_achievements_1 = get_new_achievements(self.member1, [self.product_beer])

        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 5, 13, 13, 1, 0))):
            new_achievements_2 = get_new_achievements(self.member1, [self.product_beer])

        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 5, 14, 12, 50, 0))):
            new_achievements_3 = get_new_achievements(self.member1, [self.product_beer])

        self.assertIn(self.achievement_beer_drinker, new_achievements_1)
        self.assertNotIn(self.achievement_beer_drinker, new_achievements_2)
        self.assertNotIn(self.achievement_beer_drinker, new_achievements_3)

    def test_new_achievements_require_all_tasks_and_constraints(self):

        constraint = AchievementConstraint.objects.create(  # An AchievementConstraint that covers all days
            month_start=5,  # Only May
            month_end=5,
            day_start=12,
            day_end=13,
            time_start=datetime.time(12, 00),
            time_end=datetime.time(13, 00),
        )

        self.achievement_better_beer_drinker.constraints.add(constraint)

        # Is not the correct month
        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 4, 12, 12, 1))):
            self.create_sale()

        # Is within the achievement constraint
        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 5, 12, 12, 1))):
            self.create_sale()

        # get_new_achievements is called within the achievement constraint
        # (the output should not contain the achievement, as it needs TWO beer sales)
        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 5, 13, 12, 50, 0))):
            new_achievements_1 = get_new_achievements(self.member1, [self.product_beer])

        # Is within the achievement constraint
        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 5, 12, 12, 5))):
            self.create_sale()

        # get_new_achievements is called within the achievement constraint
        # (The output should contain the achievement now)
        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 5, 13, 12, 50, 0))):
            new_achievements_2 = get_new_achievements(self.member1, [self.product_beer])

        self.assertNotIn(self.achievement_better_beer_drinker, new_achievements_1)
        self.assertIn(self.achievement_better_beer_drinker, new_achievements_2)

    def test_get_new_achievements_weekday_constraint(self):
        constraint = AchievementConstraint.objects.create(weekday=3)  # Thursday
        self.achievement_beer_drinker.constraints.add(constraint)

        # This day is a Wednesday
        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 5, 14))):
            self.create_sale()

        # A Thursday (Should not return beer_drinker achievement)
        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 5, 15))):
            new_achievements_1 = get_new_achievements(self.member1, [self.product_beer])

        # This day is a Thursday
        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 5, 15))):
            self.create_sale()

        # A Thursday (Should return beer_drinker achievement)
        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 5, 15))):
            new_achievements_2 = get_new_achievements(self.member1, [self.product_beer])

        self.assertNotIn(self.achievement_beer_drinker, new_achievements_1)
        self.assertIn(self.achievement_beer_drinker, new_achievements_2)

    def test_get_new_achievements_does_not_return_completed_achievements(self):
        AchievementComplete.objects.create(member=self.member1, achievement=self.achievement_beer_drinker)

        self.create_sale()
        self.create_sale()

        new_achievements = get_new_achievements(self.member1, [self.product_beer])

        self.assertNotIn(self.achievement_beer_drinker, new_achievements)
        self.assertIn(self.achievement_better_beer_drinker, new_achievements)

    def test_get_acquired_achievements_returns_correct_achievements(self):
        self.create_achievement_complete(self.achievement_beer_drinker)
        acquired_achievements_1 = list(get_acquired_achievements_with_rarity(self.member1))

        self.create_achievement_complete(self.achievement_better_beer_drinker)
        acquired_achievements_2 = list(get_acquired_achievements_with_rarity(self.member1))

        self.assertIn(self.achievement_beer_drinker, [x[0] for x in acquired_achievements_1])
        self.assertNotIn(self.achievement_better_beer_drinker, [x[0] for x in acquired_achievements_1])

        self.assertIn(self.achievement_beer_drinker, [x[0] for x in acquired_achievements_2])
        self.assertIn(self.achievement_better_beer_drinker, [x[0] for x in acquired_achievements_2])

    def test_get_missing_achievements_returns_correct_achievements(self):
        self.create_achievement_complete(self.achievement_beer_drinker)
        acquired_achievements_1 = list(get_missing_achievements(self.member1))

        self.create_achievement_complete(self.achievement_better_beer_drinker)
        acquired_achievements_2 = list(get_missing_achievements(self.member1))

        self.assertNotIn(self.achievement_beer_drinker, acquired_achievements_1)
        self.assertIn(self.achievement_better_beer_drinker, acquired_achievements_1)

        self.assertNotIn(self.achievement_beer_drinker, acquired_achievements_2)
        self.assertNotIn(self.achievement_better_beer_drinker, acquired_achievements_2)

    def test_get_user_leaderboard_position_returns_correct_percentage(self):

        # Of all members with achievements, this member has the lowest amount (top 100%)
        self.create_achievement_complete(self.achievement_beer_drinker, self.member2)

        # This user has the most achievements, but since only 2 has achievements, he is top 50%
        self.create_achievement_complete(self.achievement_beer_drinker, self.member3)
        self.create_achievement_complete(self.achievement_better_beer_drinker, self.member3)

        top_percentage_1 = get_user_leaderboard_position(self.member1)
        top_percentage_2 = get_user_leaderboard_position(self.member2)
        top_percentage_3 = get_user_leaderboard_position(self.member3)

        self.assertEqual(top_percentage_1, 100.0)  # A member with no achievements is always top 100%
        self.assertEqual(top_percentage_2, 100.0)
        self.assertEqual(top_percentage_3, 50.0)


class AchievementEdgeCaseTests(TestCase):
    def setUp(self):
        self.member = Member.objects.create(username="testuser", balance=100)
        self.category = Category.objects.create(name="Test Category")
        self.product = Product.objects.create(name="Test Product", price=10, active=True)
        self.product.categories.add(self.category)

        self.cph_tz = pytz.timezone("Europe/Copenhagen")

    def test_get_new_achievements_for_any_purchase(self):
        """Test getting an achievement for buying any product (any_purchase task type)"""
        # Create a task that triggers on any purchase
        task = AchievementTask.objects.create(task_type="any_purchase", goal_value=1)

        # Create achievement with the any_purchase task
        achievement = Achievement.objects.create(title="First Purchase", description="Make your first purchase")
        achievement.tasks.add(task)

        # Create a sale
        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 5, 15, 12, 0))):
            Sale.objects.create(member=self.member, product=self.product, price=10)

        # Check that the achievement is awarded
        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 5, 15, 12, 1))):
            new_achievements = get_new_achievements(self.member, [self.product])
            self.assertIn(achievement, new_achievements)

    def test_get_new_achievements_for_any_purchase_multiple_required(self):
        """Test getting an achievement that requires multiple purchases"""
        # Create a task that requires 3 purchases
        task = AchievementTask.objects.create(task_type="any_purchase", goal_value=3)

        # Create achievement
        achievement = Achievement.objects.create(title="Frequent Buyer", description="Make 3 purchases")
        achievement.tasks.add(task)

        # Create 2 sales (not enough)
        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 5, 15, 12, 0))):
            Sale.objects.create(member=self.member, product=self.product, price=10)
            Sale.objects.create(member=self.member, product=self.product, price=10)

        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 5, 15, 12, 1))):
            new_achievements = get_new_achievements(self.member, [self.product])
            self.assertNotIn(achievement, new_achievements)

        # Create 3rd sale (should trigger achievement)
        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 5, 15, 13, 0))):
            Sale.objects.create(member=self.member, product=self.product, price=10)

        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 5, 15, 13, 1))):
            new_achievements = get_new_achievements(self.member, [self.product])
            self.assertIn(achievement, new_achievements)

    def test_get_new_achievements_with_multiple_tasks(self):
        # Create achievement with multiple tasks
        task1 = AchievementTask.objects.create(task_type="product", product=self.product, goal_value=1)
        task2 = AchievementTask.objects.create(task_type="category", category=self.category, goal_value=1)

        achievement = Achievement.objects.create(title="Multi-Task Achievement", description="Complete multiple tasks")
        achievement.tasks.add(task1, task2)

        # Create sale
        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 5, 15, 12, 0))):
            Sale.objects.create(member=self.member, product=self.product, price=10)

        # Should complete achievement since both tasks are satisfied
        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 5, 15, 12, 1))):
            new_achievements = get_new_achievements(self.member, [self.product])
            self.assertIn(achievement, new_achievements)

    def test_get_new_achievements_with_active_duration(self):
        task = AchievementTask.objects.create(task_type="product", product=self.product, goal_value=2)

        achievement = Achievement.objects.create(
            title="Time-Limited Achievement",
            description="Complete within time limit",
            active_duration=datetime.timedelta(hours=1),
        )
        achievement.tasks.add(task)

        # Create sales within time window
        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 5, 15, 12, 0))):
            Sale.objects.create(member=self.member, product=self.product, price=10)

        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 5, 15, 12, 30))):
            Sale.objects.create(member=self.member, product=self.product, price=10)

        # Should complete achievement
        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 5, 15, 12, 31))):
            new_achievements = get_new_achievements(self.member, [self.product])
            self.assertIn(achievement, new_achievements)

    def test_get_new_achievements_with_active_from(self):
        task = AchievementTask.objects.create(task_type="product", product=self.product, goal_value=1)

        achievement = Achievement.objects.create(
            title="Future Achievement",
            description="Only active from specific date",
            active_from=self.cph_tz.localize(datetime.datetime(2025, 6, 1)),
        )
        achievement.tasks.add(task)

        # Create sale before active_from
        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 5, 15, 12, 0))):
            Sale.objects.create(member=self.member, product=self.product, price=10)

        # Should not complete achievement (before active_from)
        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 5, 15, 12, 1))):
            new_achievements = get_new_achievements(self.member, [self.product])
            self.assertNotIn(achievement, new_achievements)

        # Create another sale after active_from
        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 6, 1, 12, 0))):
            Sale.objects.create(member=self.member, product=self.product, price=10)

        # Should complete achievement (after active_from)
        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 6, 1, 12, 1))):
            new_achievements = get_new_achievements(self.member, [self.product])
            self.assertIn(achievement, new_achievements)

    def test_get_acquired_achievements_with_rarity_edge_cases(self):
        # Create multiple achievements
        task1 = AchievementTask.objects.create(task_type="product", product=self.product, goal_value=1)
        achievement1 = Achievement.objects.create(title="Common Achievement", description="Easy to get")
        achievement1.tasks.add(task1)

        task2 = AchievementTask.objects.create(task_type="product", product=self.product, goal_value=5)
        achievement2 = Achievement.objects.create(title="Rare Achievement", description="Hard to get")
        achievement2.tasks.add(task2)

        # Create multiple members
        member2 = Member.objects.create(username="testuser2", balance=100)
        member3 = Member.objects.create(username="testuser3", balance=100)

        # Member 1 gets both achievements
        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 5, 15, 12, 0))):
            for _ in range(5):
                Sale.objects.create(member=self.member, product=self.product, price=10)

            # Trigger achievement completion
            get_new_achievements(self.member, [self.product])

        # Member 2 gets only common achievement
        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 5, 15, 12, 0))):
            Sale.objects.create(member=member2, product=self.product, price=10)
            get_new_achievements(member2, [self.product])

        # Member 3 gets no achievements

        # Test rarity calculations
        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 5, 15, 13, 0))):
            # Member 1 should have both achievements
            achievements = get_acquired_achievements_with_rarity(self.member)
            achievement_titles = [a[0].title for a in achievements]
            self.assertIn("Common Achievement", achievement_titles)
            self.assertIn("Rare Achievement", achievement_titles)

            # Check rarity percentages
            for achievement, rarity in achievements:
                if achievement.title == "Common Achievement":
                    self.assertEqual(rarity, 100.0)  # 2 out of 2 members who have any achievements
                elif achievement.title == "Rare Achievement":
                    self.assertEqual(rarity, 50.0)  # 1 out of 2 members who have any achievements

    def test_get_missing_achievements_edge_cases(self):
        # Create multiple achievements
        task1 = AchievementTask.objects.create(task_type="product", product=self.product, goal_value=1)
        achievement1 = Achievement.objects.create(title="Easy Achievement", description="Easy to get")
        achievement1.tasks.add(task1)

        task2 = AchievementTask.objects.create(task_type="product", product=self.product, goal_value=10)
        achievement2 = Achievement.objects.create(title="Hard Achievement", description="Hard to get")
        achievement2.tasks.add(task2)

        # Member gets easy achievement
        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 5, 15, 12, 0))):
            Sale.objects.create(member=self.member, product=self.product, price=10)
            # Trigger achievement completion
            get_new_achievements(self.member, [self.product])

        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 5, 15, 12, 1))):
            missing = get_missing_achievements(self.member)
            missing_titles = [a.title for a in missing]

            self.assertNotIn("Easy Achievement", missing_titles)
            self.assertIn("Hard Achievement", missing_titles)

    def test_leaderboard_position_tie_breaking(self):
        # Create multiple members with same number of achievements
        member2 = Member.objects.create(username="testuser2", balance=100)
        member3 = Member.objects.create(username="testuser3", balance=100)

        task = AchievementTask.objects.create(task_type="product", product=self.product, goal_value=1)
        achievement = Achievement.objects.create(title="Test Achievement", description="Test")
        achievement.tasks.add(task)

        # All members get the achievement
        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 5, 15, 12, 0))):
            Sale.objects.create(member=self.member, product=self.product, price=10)
            Sale.objects.create(member=member2, product=self.product, price=10)
            Sale.objects.create(member=member3, product=self.product, price=10)

        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 5, 15, 12, 1))):
            # All should have same position (tie)
            pos1 = get_user_leaderboard_position(self.member)
            pos2 = get_user_leaderboard_position(member2)
            pos3 = get_user_leaderboard_position(member3)

            self.assertEqual(pos1, pos2)
            self.assertEqual(pos2, pos3)
            self.assertEqual(pos1, 100.0)  # All tied for first place

    def test_leaderboard_position_rank_gaps_bug(self):
        """
        Test for the bug where current_rank increments every iteration
        regardless of ties, creating rank gaps.
        """
        # Create members with different achievement counts to expose the bug
        member2 = Member.objects.create(username="testuser2", balance=100)
        member3 = Member.objects.create(username="testuser3", balance=100)
        member4 = Member.objects.create(username="testuser4", balance=100)

        # Create achievements
        task1 = AchievementTask.objects.create(task_type="product", product=self.product, goal_value=1)
        achievement1 = Achievement.objects.create(title="Easy Achievement", description="Easy")
        achievement1.tasks.add(task1)

        task2 = AchievementTask.objects.create(task_type="product", product=self.product, goal_value=2)
        achievement2 = Achievement.objects.create(title="Hard Achievement", description="Hard")
        achievement2.tasks.add(task2)

        # Member 1: 2 achievements (should be rank 1)
        # Member 2: 2 achievements (should be rank 1 - tie)
        # Member 3: 1 achievement (should be rank 2)
        # Member 4: 0 achievements (should be rank 3 or 100%)

        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 5, 15, 12, 0))):
            # Member 1 gets 2 achievements
            Sale.objects.create(member=self.member, product=self.product, price=10)
            get_new_achievements(self.member, [self.product])  # Should complete achievement1
            Sale.objects.create(member=self.member, product=self.product, price=10)
            get_new_achievements(self.member, [self.product])  # Should complete achievement2

            # Member 2 gets 2 achievements
            Sale.objects.create(member=member2, product=self.product, price=10)
            get_new_achievements(member2, [self.product])  # Should complete achievement1
            Sale.objects.create(member=member2, product=self.product, price=10)
            get_new_achievements(member2, [self.product])  # Should complete achievement2

            # Member 3 gets 1 achievement
            Sale.objects.create(member=member3, product=self.product, price=10)
            get_new_achievements(member3, [self.product])  # Should complete achievement1 only

            # Member 4 gets no achievements

        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 5, 15, 13, 0))):
            # Debug: Check actual achievement counts
            from achievements.models import AchievementComplete
            from django.db.models import Count

            leaderboard = (
                AchievementComplete.objects.all()
                .values('member')
                .annotate(total=Count('id'))
                .order_by('-total', 'member')
            )

            print("Leaderboard data:")
            for entry in leaderboard:
                print(f"Member {entry['member']}: {entry['total']} achievements")

            pos1 = get_user_leaderboard_position(self.member)  # Should be 100% (rank 1)
            pos2 = get_user_leaderboard_position(member2)  # Should be 100% (rank 1, tie)
            pos3 = get_user_leaderboard_position(member3)  # Should be 50% (rank 2)
            pos4 = get_user_leaderboard_position(member4)  # Should be 0% (rank 3)

            print(f"Positions: member1={pos1}, member2={pos2}, member3={pos3}, member4={pos4}")

            # With the bug, these assertions might fail due to incorrect rank calculation
            self.assertEqual(pos1, 33.33)
            self.assertEqual(pos2, 33.33)
            self.assertEqual(pos3, 100.0)
            self.assertEqual(pos4, 100.0)

class ImpossibleTaskTests(TestCase):
    def setUp(self) -> None:
        self.member = Member.objects.create(username="testuser", balance=100)
        self.product = Product.objects.create(name="Beer", price=10, active=True)
        self.impossible_task = AchievementTask.objects.create(
            task_type=AchievementTask.IMPOSSIBLE_TASK_TYPE, goal_value=1
        )

    def test_is_never_relevant(self) -> None:
        self.assertFalse(self.impossible_task.is_relevant([self.product]))

    def test_is_never_completed(self) -> None:
        self.assertFalse(_is_completed(self.impossible_task, self.member))

    def test_clean_skips_validation(self) -> None:
        task = AchievementTask(task_type=AchievementTask.IMPOSSIBLE_TASK_TYPE, goal_value=0)
        task.full_clean()

    def test_blocks_achievement_when_other_tasks_are_completed(self) -> None:
        any_purchase_task = AchievementTask.objects.create(
            task_type=AchievementTask.ANY_PURCHASE_TASK_TYPE, goal_value=1
        )
        achievement = _create_achievement("Blocked", any_purchase_task, self.impossible_task)
        _create_sale(self.member, self.product, _cph(2025, 5, 15, 12, 0))

        with freeze_time(_cph(2025, 5, 15, 12, 1)):
            new_achievements = get_new_achievements(self.member, [self.product])

        self.assertNotIn(achievement, new_achievements)

    def test_achievement_with_only_impossible_task_is_never_awarded(self) -> None:
        achievement = _create_achievement("Impossible", self.impossible_task)
        _create_sale(self.member, self.product, _cph(2025, 5, 15, 12, 0))

        with freeze_time(_cph(2025, 5, 15, 12, 1)):
            new_achievements = get_new_achievements(self.member, [self.product])

        self.assertNotIn(achievement, new_achievements)


class TimeAsMemberTaskTests(TestCase):
    def setUp(self) -> None:
        self.product = Product.objects.create(name="Beer", price=10, active=True)

    def test_is_relevant_for_any_product(self) -> None:
        task = AchievementTask(task_type=AchievementTask.TIME_AS_MEMBER_TASK_TYPE, goal_value=1)

        self.assertTrue(task.is_relevant([self.product]))

    def test_completed_when_member_is_old_enough(self) -> None:
        with freeze_time(_cph(2025, 1, 1, 12, 0)):
            member = Member.objects.create(username="testuser")
        task = AchievementTask(
            task_type=AchievementTask.TIME_AS_MEMBER_TASK_TYPE, goal_value=24 * 60 * 60  # 1 day
        )

        with freeze_time(_cph(2025, 1, 3, 12, 0)):
            self.assertTrue(_is_completed(task, member))

    def test_completed_at_exact_threshold(self) -> None:
        with freeze_time(_cph(2025, 1, 1, 12, 0)):
            member = Member.objects.create(username="testuser")
        task = AchievementTask(task_type=AchievementTask.TIME_AS_MEMBER_TASK_TYPE, goal_value=3600)

        with freeze_time(_cph(2025, 1, 1, 13, 0)):
            self.assertTrue(_is_completed(task, member))

    def test_not_completed_when_member_is_too_young(self) -> None:
        with freeze_time(_cph(2025, 1, 1, 12, 0)):
            member = Member.objects.create(username="testuser")
        task = AchievementTask(task_type=AchievementTask.TIME_AS_MEMBER_TASK_TYPE, goal_value=3600)

        with freeze_time(_cph(2025, 1, 1, 12, 30)):
            self.assertFalse(_is_completed(task, member))

    def test_default_creation_date_never_completes(self) -> None:
        member = Member.objects.create(username="testuser")
        member.created_at = datetime.datetime(1976, 2, 1, 0, 0, tzinfo=datetime.timezone.utc)
        task = AchievementTask(task_type=AchievementTask.TIME_AS_MEMBER_TASK_TYPE, goal_value=1)

        with freeze_time(_cph(2025, 1, 1, 12, 0)):
            self.assertFalse(_is_completed(task, member))

    def test_clean_rejects_non_positive_goal(self) -> None:
        task = AchievementTask(task_type=AchievementTask.TIME_AS_MEMBER_TASK_TYPE, goal_value=0)

        with self.assertRaises(ValidationError):
            task.full_clean()

    def test_clean_rejects_product(self) -> None:
        task = AchievementTask(
            task_type=AchievementTask.TIME_AS_MEMBER_TASK_TYPE, product=self.product, goal_value=1
        )

        with self.assertRaises(ValidationError):
            task.full_clean()


class TopXInCategoryTaskTests(TestCase):
    def setUp(self) -> None:
        self.member = Member.objects.create(username="testuser", balance=100)
        self.category_beer = Category.objects.create(name="Beer Category")
        self.category_soda = Category.objects.create(name="Soda Category")
        self.product_beer = Product.objects.create(name="Beer", price=10, active=True)
        self.product_beer.categories.add(self.category_beer)
        self.product_soda = Product.objects.create(name="Soda", price=5, active=True)
        self.product_soda.categories.add(self.category_soda)

    def test_month_completed_when_rank_is_within_goal(self) -> None:
        task = self._create_task(AchievementTask.TOP_X_IN_CATEGORY_MONTH_TASK_TYPE, self.category_beer, 3)
        rankings: Rankings = {self.category_beer: self._ranking(2, 10)}

        self.assertTrue(_is_completed(task, self.member, rankings_month=rankings))

    def test_month_completed_when_rank_equals_goal(self) -> None:
        task = self._create_task(AchievementTask.TOP_X_IN_CATEGORY_MONTH_TASK_TYPE, self.category_beer, 3)
        rankings: Rankings = {self.category_beer: self._ranking(3, 10)}

        self.assertTrue(_is_completed(task, self.member, rankings_month=rankings))

    def test_month_not_completed_when_rank_is_outside_goal(self) -> None:
        task = self._create_task(AchievementTask.TOP_X_IN_CATEGORY_MONTH_TASK_TYPE, self.category_beer, 3)
        rankings: Rankings = {self.category_beer: self._ranking(4, 10)}

        self.assertFalse(_is_completed(task, self.member, rankings_month=rankings))

    def test_rank_zero_is_not_completed(self) -> None:
        task = self._create_task(AchievementTask.TOP_X_IN_CATEGORY_MONTH_TASK_TYPE, self.category_beer, 3)
        rankings: Rankings = {self.category_beer: self._ranking(0, 0)}

        self.assertFalse(_is_completed(task, self.member, rankings_month=rankings))

    def test_not_completed_when_category_is_missing_from_rankings(self) -> None:
        task = self._create_task(AchievementTask.TOP_X_IN_CATEGORY_MONTH_TASK_TYPE, self.category_beer, 3)
        rankings: Rankings = {self.category_soda: self._ranking(1, 10)}

        self.assertFalse(_is_completed(task, self.member, rankings_month=rankings))

    def test_month_task_ignores_year_rankings(self) -> None:
        task = self._create_task(AchievementTask.TOP_X_IN_CATEGORY_MONTH_TASK_TYPE, self.category_beer, 3)
        year_rankings: Rankings = {self.category_beer: self._ranking(1, 10)}
        month_rankings: Rankings = {self.category_beer: self._ranking(9, 10)}

        self.assertFalse(
            _is_completed(task, self.member, rankings_year=year_rankings, rankings_month=month_rankings)
        )

    def test_year_completed_when_rank_is_within_goal(self) -> None:
        task = self._create_task(AchievementTask.TOP_X_IN_CATEGORY_YEAR_TASK_TYPE, self.category_beer, 3)
        year_rankings: Rankings = {self.category_beer: self._ranking(1, 10)}
        month_rankings: Rankings = {self.category_beer: self._ranking(9, 10)}

        self.assertTrue(
            _is_completed(task, self.member, rankings_year=year_rankings, rankings_month=month_rankings)
        )

    def test_year_task_ignores_month_rankings(self) -> None:
        task = self._create_task(AchievementTask.TOP_X_IN_CATEGORY_YEAR_TASK_TYPE, self.category_beer, 3)
        year_rankings: Rankings = {self.category_beer: self._ranking(9, 10)}
        month_rankings: Rankings = {self.category_beer: self._ranking(1, 10)}

        self.assertFalse(
            _is_completed(task, self.member, rankings_year=year_rankings, rankings_month=month_rankings)
        )

    def test_without_category_completes_when_top_in_any_category(self) -> None:
        task = self._create_task(AchievementTask.TOP_X_IN_CATEGORY_MONTH_TASK_TYPE, None, 3)
        rankings: Rankings = {self.category_beer: self._ranking(9, 10), self.category_soda: self._ranking(2, 10)}

        self.assertTrue(_is_completed(task, self.member, rankings_month=rankings))

    def test_without_category_not_completed_when_outside_top_in_all(self) -> None:
        task = self._create_task(AchievementTask.TOP_X_IN_CATEGORY_MONTH_TASK_TYPE, None, 3)
        rankings: Rankings = {self.category_beer: self._ranking(9, 10), self.category_soda: self._ranking(4, 10)}

        self.assertFalse(_is_completed(task, self.member, rankings_month=rankings))

    def test_without_category_ignores_rank_zero(self) -> None:
        task = self._create_task(AchievementTask.TOP_X_IN_CATEGORY_MONTH_TASK_TYPE, None, 3)
        rankings: Rankings = {self.category_beer: self._ranking(0, 0)}

        self.assertFalse(_is_completed(task, self.member, rankings_month=rankings))

    def test_without_category_not_completed_with_empty_rankings(self) -> None:
        task = self._create_task(AchievementTask.TOP_X_IN_CATEGORY_YEAR_TASK_TYPE, None, 3)

        self.assertFalse(_is_completed(task, self.member))

    def test_is_relevant_for_product_in_category(self) -> None:
        task = self._create_task(AchievementTask.TOP_X_IN_CATEGORY_MONTH_TASK_TYPE, self.category_beer, 3)

        self.assertTrue(task.is_relevant([self.product_beer]))
        self.assertFalse(task.is_relevant([self.product_soda]))

    def test_without_category_is_relevant_for_any_product(self) -> None:
        task = self._create_task(AchievementTask.TOP_X_IN_CATEGORY_YEAR_TASK_TYPE, None, 3)

        self.assertTrue(task.is_relevant([self.product_beer]))
        self.assertTrue(task.is_relevant([self.product_soda]))

    def test_clean_rejects_product(self) -> None:
        task = AchievementTask(
            task_type=AchievementTask.TOP_X_IN_CATEGORY_MONTH_TASK_TYPE,
            product=self.product_beer,
            goal_value=3,
        )

        with self.assertRaises(ValidationError):
            task.full_clean()

    def test_clean_rejects_non_positive_goal(self) -> None:
        task = AchievementTask(
            task_type=AchievementTask.TOP_X_IN_CATEGORY_YEAR_TASK_TYPE,
            category=self.category_beer,
            goal_value=0,
        )

        with self.assertRaises(ValidationError):
            task.full_clean()

    def _create_task(self, task_type: str, category: Category | None, goal_value: int) -> AchievementTask:
        return AchievementTask.objects.create(task_type=task_type, category=category, goal_value=goal_value)

    def _ranking(self, rank: int, total: int = 10) -> tuple[tuple[int, int], str, int]:
        my_count: int = 0 if rank == 0 else 1
        return (rank, total), "0.00", my_count

class StreakDaysTaskTests(TestCase):
    def setUp(self) -> None:
        self.member = Member.objects.create(username="testuser", balance=100)
        self.other_member = Member.objects.create(username="otheruser", balance=100)
        self.product = Product.objects.create(name="Beer", price=10, active=True)

    def test_is_relevant_for_any_product(self) -> None:
        task = self._create_task(3)

        self.assertTrue(task.is_relevant([self.product]))

    def test_completed_with_consecutive_days_ending_today(self) -> None:
        for day in (13, 14, 15):
            _create_sale(self.member, self.product, _cph(2025, 5, day, 12, 0))
        task = self._create_task(3)

        with freeze_time(_cph(2025, 5, 15, 18, 0)):
            self.assertTrue(_is_completed(task, self.member))

    def test_single_day_streak_completes_with_purchase_today(self) -> None:
        _create_sale(self.member, self.product, _cph(2025, 5, 15, 12, 0))
        task = self._create_task(1)

        with freeze_time(_cph(2025, 5, 15, 18, 0)):
            self.assertTrue(_is_completed(task, self.member))

    def test_not_completed_with_gap_in_streak(self) -> None:
        for day in (13, 15):
            _create_sale(self.member, self.product, _cph(2025, 5, day, 12, 0))
        task = self._create_task(3)

        with freeze_time(_cph(2025, 5, 15, 18, 0)):
            self.assertFalse(_is_completed(task, self.member))

    def test_multiple_sales_on_same_day_count_once(self) -> None:
        for hour in (10, 12, 14):
            _create_sale(self.member, self.product, _cph(2025, 5, 15, hour, 0))
        task = self._create_task(3)

        with freeze_time(_cph(2025, 5, 15, 18, 0)):
            self.assertFalse(_is_completed(task, self.member))

    def test_not_completed_when_streak_ended_before_today(self) -> None:
        for day in (10, 11, 12):
            _create_sale(self.member, self.product, _cph(2025, 5, day, 12, 0))
        task = self._create_task(3)

        with freeze_time(_cph(2025, 5, 15, 18, 0)):
            self.assertFalse(_is_completed(task, self.member))

    def test_sales_older_than_window_do_not_break_completion(self) -> None:
        for day in (12, 13, 14, 15):
            _create_sale(self.member, self.product, _cph(2025, 5, day, 12, 0))
        task = self._create_task(3)

        with freeze_time(_cph(2025, 5, 15, 18, 0)):
            self.assertTrue(_is_completed(task, self.member))

    def test_window_starts_at_local_midnight(self) -> None:
        _create_sale(self.member, self.product, _cph(2025, 5, 13, 0, 30))
        _create_sale(self.member, self.product, _cph(2025, 5, 14, 12, 0))
        _create_sale(self.member, self.product, _cph(2025, 5, 15, 12, 0))
        task = self._create_task(3)

        with freeze_time(_cph(2025, 5, 15, 18, 0)):
            self.assertTrue(_is_completed(task, self.member))

    def test_sale_just_before_window_does_not_count(self) -> None:
        _create_sale(self.member, self.product, _cph(2025, 5, 12, 23, 30))
        _create_sale(self.member, self.product, _cph(2025, 5, 14, 12, 0))
        _create_sale(self.member, self.product, _cph(2025, 5, 15, 12, 0))
        task = self._create_task(3)

        with freeze_time(_cph(2025, 5, 15, 18, 0)):
            self.assertFalse(_is_completed(task, self.member))

    def test_other_members_sales_do_not_count(self) -> None:
        _create_sale(self.other_member, self.product, _cph(2025, 5, 14, 12, 0))
        _create_sale(self.member, self.product, _cph(2025, 5, 15, 12, 0))
        task = self._create_task(2)

        with freeze_time(_cph(2025, 5, 15, 18, 0)):
            self.assertFalse(_is_completed(task, self.member))

    def test_get_new_achievements_awards_streak(self) -> None:
        achievement = _create_achievement("Streak", self._create_task(2))
        _create_sale(self.member, self.product, _cph(2025, 5, 14, 12, 0))
        _create_sale(self.member, self.product, _cph(2025, 5, 15, 12, 0))

        with freeze_time(_cph(2025, 5, 15, 12, 1)):
            new_achievements = get_new_achievements(self.member, [self.product])

        self.assertIn(achievement, new_achievements)

    def test_get_new_achievements_does_not_award_broken_streak(self) -> None:
        achievement = _create_achievement("Streak", self._create_task(2))
        _create_sale(self.member, self.product, _cph(2025, 5, 13, 12, 0))
        _create_sale(self.member, self.product, _cph(2025, 5, 15, 12, 0))

        with freeze_time(_cph(2025, 5, 15, 12, 1)):
            new_achievements = get_new_achievements(self.member, [self.product])

        self.assertNotIn(achievement, new_achievements)

    def _create_task(self, goal_value: int) -> AchievementTask:
        return AchievementTask.objects.create(
            task_type=AchievementTask.STREAK_DAYS_TASK_TYPE, goal_value=goal_value
        )


class FirstPurchaseTaskTests(TestCase):
    """2025-05-12 is a Monday, 2025-05-14 a Wednesday."""

    def setUp(self) -> None:
        self.member = Member.objects.create(username="testuser", balance=100)
        self.other_member = Member.objects.create(username="otheruser", balance=100)
        self.product = Product.objects.create(name="Beer", price=10, active=True)

    def test_is_relevant_for_any_product(self) -> None:
        self.assertTrue(self._create_day_task().is_relevant([self.product]))
        self.assertTrue(self._create_week_task().is_relevant([self.product]))

    def test_day_completed_for_first_buyer(self) -> None:
        _create_sale(self.member, self.product, _cph(2025, 5, 14, 8, 0))
        _create_sale(self.other_member, self.product, _cph(2025, 5, 14, 9, 0))

        with freeze_time(_cph(2025, 5, 14, 12, 0)):
            self.assertTrue(_is_completed(self._create_day_task(), self.member))

    def test_day_not_completed_when_other_member_bought_first(self) -> None:
        _create_sale(self.other_member, self.product, _cph(2025, 5, 14, 8, 0))
        _create_sale(self.member, self.product, _cph(2025, 5, 14, 9, 0))

        with freeze_time(_cph(2025, 5, 14, 12, 0)):
            self.assertFalse(_is_completed(self._create_day_task(), self.member))

    def test_day_ignores_sales_from_previous_days(self) -> None:
        _create_sale(self.other_member, self.product, _cph(2025, 5, 13, 8, 0))
        _create_sale(self.member, self.product, _cph(2025, 5, 14, 9, 0))

        with freeze_time(_cph(2025, 5, 14, 12, 0)):
            self.assertTrue(_is_completed(self._create_day_task(), self.member))

    def test_day_starts_at_local_midnight(self) -> None:
        _create_sale(self.other_member, self.product, _cph(2025, 5, 13, 23, 59))
        _create_sale(self.member, self.product, _cph(2025, 5, 14, 0, 1))

        with freeze_time(_cph(2025, 5, 14, 12, 0)):
            self.assertTrue(_is_completed(self._create_day_task(), self.member))

    def test_week_not_completed_when_other_member_bought_earlier_this_week(self) -> None:
        _create_sale(self.other_member, self.product, _cph(2025, 5, 12, 9, 0))
        _create_sale(self.member, self.product, _cph(2025, 5, 14, 9, 0))

        with freeze_time(_cph(2025, 5, 14, 12, 0)):
            self.assertFalse(_is_completed(self._create_week_task(), self.member))

    def test_week_completed_for_first_buyer_of_the_week(self) -> None:
        _create_sale(self.member, self.product, _cph(2025, 5, 12, 9, 0))
        _create_sale(self.other_member, self.product, _cph(2025, 5, 14, 9, 0))

        with freeze_time(_cph(2025, 5, 14, 12, 0)):
            self.assertTrue(_is_completed(self._create_week_task(), self.member))

    def test_week_starts_on_monday(self) -> None:
        _create_sale(self.other_member, self.product, _cph(2025, 5, 11, 23, 59))  # Sunday
        _create_sale(self.member, self.product, _cph(2025, 5, 12, 0, 1))  # Monday

        with freeze_time(_cph(2025, 5, 14, 12, 0)):
            self.assertTrue(_is_completed(self._create_week_task(), self.member))

    def test_first_of_day_but_not_first_of_week(self) -> None:
        _create_sale(self.other_member, self.product, _cph(2025, 5, 12, 9, 0))
        _create_sale(self.member, self.product, _cph(2025, 5, 14, 9, 0))

        with freeze_time(_cph(2025, 5, 14, 12, 0)):
            self.assertTrue(_is_completed(self._create_day_task(), self.member))
            self.assertFalse(_is_completed(self._create_week_task(), self.member))

    def test_not_completed_without_any_sales(self) -> None:
        with freeze_time(_cph(2025, 5, 14, 12, 0)):
            self.assertFalse(_is_completed(self._create_day_task(), self.member))
            self.assertFalse(_is_completed(self._create_week_task(), self.member))

    def test_get_new_achievements_awards_only_first_buyer_of_the_day(self) -> None:
        achievement = _create_achievement("Early Bird", self._create_day_task())
        _create_sale(self.member, self.product, _cph(2025, 5, 14, 8, 0))
        _create_sale(self.other_member, self.product, _cph(2025, 5, 14, 9, 0))

        with freeze_time(_cph(2025, 5, 14, 9, 1)):
            first_buyer_achievements = get_new_achievements(self.member, [self.product])
            second_buyer_achievements = get_new_achievements(self.other_member, [self.product])

        self.assertIn(achievement, first_buyer_achievements)
        self.assertNotIn(achievement, second_buyer_achievements)

    def _create_day_task(self) -> AchievementTask:
        return AchievementTask.objects.create(
            task_type=AchievementTask.FIRST_PURCHASE_OF_DAY_TASK_TYPE, goal_value=1
        )

    def _create_week_task(self) -> AchievementTask:
        return AchievementTask.objects.create(
            task_type=AchievementTask.FIRST_PURCHASE_OF_WEEK_TASK_TYPE, goal_value=1
        )


def _cph(year: int, month: int, day: int, hour: int = 12, minute: int = 0) -> datetime.datetime:
    return CPH_TZ.localize(datetime.datetime(year, month, day, hour, minute))


def _create_sale(member: Member, product: Product, when: datetime.datetime) -> Sale:
    with freeze_time(when):
        return Sale.objects.create(member=member, product=product, price=product.price)


def _create_achievement(title: str, *tasks: AchievementTask) -> Achievement:
    achievement = Achievement.objects.create(title=title, description=title)
    achievement.tasks.add(*tasks)
    return achievement


def _is_completed(
    task: AchievementTask,
    member: Member,
    rankings_year: Rankings | None = None,
    rankings_month: Rankings | None = None,
) -> bool:
    sales: QuerySet[Sale, Sale] = Sale.objects.filter(member=member)
    return task.is_task_completed(sales, member, rankings_year or {}, rankings_month or {})