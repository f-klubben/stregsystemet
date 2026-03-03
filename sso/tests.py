from django.contrib.auth.models import User
from django.test import TestCase

from stregsystem.models import Member


class MemberLoginTests(TestCase):
    def setUp(self):
        self.jeff = Member.objects.create(pk=1, username="jeff", firstname="jeff", lastname="jefferson", gender="M")

        self.jeff2 = Member.objects.create(pk=2, username="jeffrey", firstname="jeff", lastname="jefferson", gender="M")

    def test_generate_companion_user_twice(self):
        self.jeff.generate_companion_user()

        self.jeff.paired_user = None
        self.jeff.generate_companion_user()

    def test_generated_companion_user_unique(self):
        self.jeff.generate_companion_user()
        new_user = self.jeff.paired_user

        self.jeff.paired_user = None
        self.jeff.generate_companion_user()

        # Check that the newly generated user actually is new.
        self.assertNotEquals(self.jeff.paired_user, new_user)
