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

        self.assertTrue(task.is_relevant(self.product_beer))
        self.assertFalse(task.is_relevant(self.product_soda))

    def test_is_relevant_category_task(self):
        task = AchievementTask.objects.create(task_type="category", category=self.category_beer, goal_value=1)

        self.assertTrue(task.is_relevant(self.product_beer))
        self.assertFalse(task.is_relevant(self.product_soda))

    def test_is_relevant_any_purchase_task(self):
        task = AchievementTask.objects.create(task_type="any_purchase", goal_value=1)

        self.assertTrue(task.is_relevant(self.product_beer))
        self.assertTrue(task.is_relevant(self.product_soda))

    def test_is_relevant_alcohol_content_task(self):
        task = AchievementTask.objects.create(task_type="alcohol_content", goal_value=100)

        self.assertTrue(task.is_relevant(self.product_beer))
        self.assertFalse(task.is_relevant(self.product_soda))

    def test_is_relevant_caffeine_content_task(self):
        task = AchievementTask.objects.create(task_type="caffeine_content", goal_value=100)

        self.assertFalse(task.is_relevant(self.product_beer))
        self.assertTrue(task.is_relevant(self.product_soda))

    def test_is_relevant_used_funds_task(self):
        task = AchievementTask.objects.create(task_type="used_funds", goal_value=100)

        # used_funds and remaining_funds tasks are always relevant
        self.assertTrue(task.is_relevant(self.product_beer))
        self.assertTrue(task.is_relevant(self.product_soda))

    def test_is_relevant_remaining_funds_task(self):
        task = AchievementTask.objects.create(task_type="remaining_funds", goal_value=100)

        # used_funds and remaining_funds tasks are always relevant
        self.assertTrue(task.is_relevant(self.product_beer))
        self.assertTrue(task.is_relevant(self.product_soda))

    def test_is_task_completed_product_task(self):
        member = Member.objects.create(username="testuser", balance=100)
        task = AchievementTask.objects.create(task_type="product", product=self.product_beer, goal_value=2)

        # Create 2 sales
        Sale.objects.create(member=member, product=self.product_beer, price=10)
        Sale.objects.create(member=member, product=self.product_beer, price=10)

        sales = Sale.objects.filter(member=member, product=self.product_beer)
        self.assertTrue(task.is_task_completed(sales, member))

    def test_is_task_completed_category_task(self):
        member = Member.objects.create(username="testuser", balance=100)
        task = AchievementTask.objects.create(task_type="category", category=self.category_beer, goal_value=1)

        # Create 1 sale in beer category
        Sale.objects.create(member=member, product=self.product_beer, price=10)

        sales = Sale.objects.filter(member=member, product__categories=self.category_beer)
        self.assertTrue(task.is_task_completed(sales, member))

    def test_is_task_completed_alcohol_content_task(self):
        member = Member.objects.create(username="testuser", balance=100)
        task = AchievementTask.objects.create(task_type="alcohol_content", goal_value=500)  # 5.00 ml

        # Create sale with beer (500 ml alcohol)
        Sale.objects.create(member=member, product=self.product_beer, price=10)

        sales = Sale.objects.filter(member=member)
        self.assertTrue(task.is_task_completed(sales, member))

    def test_is_task_completed_used_funds_task(self):
        member = Member.objects.create(username="testuser", balance=100)
        task = AchievementTask.objects.create(task_type="used_funds", goal_value=50)  # 50.00 kr

        # Create sales totaling 60 kr
        Sale.objects.create(member=member, product=self.product_beer, price=30)
        Sale.objects.create(member=member, product=self.product_beer, price=30)

        sales = Sale.objects.filter(member=member)
        self.assertTrue(task.is_task_completed(sales, member))

    def test_is_task_completed_remaining_funds_task(self):
        member = Member.objects.create(username="testuser", balance=100)
        task = AchievementTask.objects.create(task_type="remaining_funds", goal_value=50)  # 50.00 kr

        # Create sale that leaves member with 70 kr (above threshold)
        Sale.objects.create(member=member, product=self.product_beer, price=30)

        sales = Sale.objects.filter(member=member)
        self.assertTrue(task.is_task_completed(sales, member))

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
        self.assertTrue(self.achievement.is_relevant_for_purchase(self.product))

        other_product = Product.objects.create(name="Other Product", price=5, active=True)
        self.assertFalse(self.achievement.is_relevant_for_purchase(other_product))

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

        new_achievements = get_new_achievements(self.member1, self.product_beer)
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
            new_achievements_1 = get_new_achievements(self.member1, self.product_beer)

        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 5, 13, 13, 1, 0))):
            new_achievements_2 = get_new_achievements(self.member1, self.product_beer)

        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 5, 14, 12, 50, 0))):
            new_achievements_3 = get_new_achievements(self.member1, self.product_beer)

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
            new_achievements_1 = get_new_achievements(self.member1, self.product_beer)

        # Is within the achievement constraint
        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 5, 12, 12, 5))):
            self.create_sale()

        # get_new_achievements is called within the achievement constraint
        # (The output should contain the achievement now)
        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 5, 13, 12, 50, 0))):
            new_achievements_2 = get_new_achievements(self.member1, self.product_beer)

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
            new_achievements_1 = get_new_achievements(self.member1, self.product_beer)

        # This day is a Thursday
        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 5, 15))):
            self.create_sale()

        # A Thursday (Should return beer_drinker achievement)
        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 5, 15))):
            new_achievements_2 = get_new_achievements(self.member1, self.product_beer)

        self.assertNotIn(self.achievement_beer_drinker, new_achievements_1)
        self.assertIn(self.achievement_beer_drinker, new_achievements_2)

    def test_get_new_achievements_does_not_return_completed_achievements(self):
        AchievementComplete.objects.create(member=self.member1, achievement=self.achievement_beer_drinker)

        self.create_sale()
        self.create_sale()

        new_achievements = get_new_achievements(self.member1, self.product_beer)

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
            new_achievements = get_new_achievements(self.member, self.product)
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
            new_achievements = get_new_achievements(self.member, self.product)
            self.assertNotIn(achievement, new_achievements)

        # Create 3rd sale (should trigger achievement)
        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 5, 15, 13, 0))):
            Sale.objects.create(member=self.member, product=self.product, price=10)

        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 5, 15, 13, 1))):
            new_achievements = get_new_achievements(self.member, self.product)
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
            new_achievements = get_new_achievements(self.member, self.product)
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
            new_achievements = get_new_achievements(self.member, self.product)
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
            new_achievements = get_new_achievements(self.member, self.product)
            self.assertNotIn(achievement, new_achievements)

        # Create another sale after active_from
        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 6, 1, 12, 0))):
            Sale.objects.create(member=self.member, product=self.product, price=10)

        # Should complete achievement (after active_from)
        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 6, 1, 12, 1))):
            new_achievements = get_new_achievements(self.member, self.product)
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
            get_new_achievements(self.member, self.product)

        # Member 2 gets only common achievement
        with freeze_time(self.cph_tz.localize(datetime.datetime(2025, 5, 15, 12, 0))):
            Sale.objects.create(member=member2, product=self.product, price=10)
            get_new_achievements(member2, self.product)

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
            get_new_achievements(self.member, self.product)

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
            get_new_achievements(self.member, self.product)  # Should complete achievement1
            Sale.objects.create(member=self.member, product=self.product, price=10)
            get_new_achievements(self.member, self.product)  # Should complete achievement2

            # Member 2 gets 2 achievements
            Sale.objects.create(member=member2, product=self.product, price=10)
            get_new_achievements(member2, self.product)  # Should complete achievement1
            Sale.objects.create(member=member2, product=self.product, price=10)
            get_new_achievements(member2, self.product)  # Should complete achievement2

            # Member 3 gets 1 achievement
            Sale.objects.create(member=member3, product=self.product, price=10)
            get_new_achievements(member3, self.product)  # Should complete achievement1 only

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

            print(f"Leaderboard data:")
            for entry in leaderboard:
                print(f"Member {entry['member']}: {entry['total']} achievements")

            pos1 = get_user_leaderboard_position(self.member)  # Should be 100% (rank 1)
            pos2 = get_user_leaderboard_position(member2)  # Should be 100% (rank 1, tie)
            pos3 = get_user_leaderboard_position(member3)  # Should be 50% (rank 2)
            pos4 = get_user_leaderboard_position(member4)  # Should be 0% (rank 3)

            print(f"Positions: member1={pos1}, member2={pos2}, member3={pos3}, member4={pos4}")

            # With the bug, these assertions might fail due to incorrect rank calculation
            self.assertEqual(pos1, 100.0)
            self.assertEqual(pos2, 100.0)
            self.assertEqual(pos3, 50.0)
            self.assertEqual(pos4, 0.0)
