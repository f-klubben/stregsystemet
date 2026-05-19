import pytz
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
