from django.contrib.auth.models import User
from django.test import TestCase

from sso.auth_backends import PasswordlessMemberBackend
from sso.models import MemberOTPRequest
from stregsystem.models import Member


class MemberLoginTests(TestCase):
    def setUp(self):
        self.jeff = Member.objects.create(pk=1, username="jeff", firstname="jeff", lastname="jefferson", gender="M")

        self.jeff2 = Member.objects.create(pk=2, username="jeffrey", firstname="jeff", lastname="jefferson", gender="M")

    def tearDown(self):
        MemberOTPRequest.objects.all().delete()

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

    def test_correct_otp_accept(self):
        MemberOTPRequest.objects.create(member=self.jeff, code="123456")

        success = self.client.login(username="jeff", otp="123456")
        self.assertTrue(success)

    def test_wrong_otp_deny(self):
        MemberOTPRequest.objects.create(member=self.jeff, code="123456")

        fail = self.client.login(username="jeff", otp="654321")
        self.assertFalse(fail)

    def test_max_tries_same_otp_deny(self):
        MemberOTPRequest.objects.create(member=self.jeff, code="123456")

        # Try logging in multiple times with same OTP
        for _ in range(PasswordlessMemberBackend.MAX_RETRIES_SAME_OTP):
            result = self.client.login(username="jeff", otp="654321")
            self.assertFalse(result)

        # Attempt with correct should fail
        fail = self.client.login(username="jeff", otp="123456")
        self.assertFalse(fail)

    def test_repeated_attempt_accept(self):
        # Should allow more than 1 wrong attempt for test to be valid
        self.assertTrue(PasswordlessMemberBackend.MAX_RETRIES_SAME_OTP > 1)

        MemberOTPRequest.objects.create(member=self.jeff, code="123456")

        # Try logging in multiple times with same OTP, but less than limit
        for _ in range(PasswordlessMemberBackend.MAX_RETRIES_SAME_OTP - 1):
            result = self.client.login(username="jeff", otp="654321")
            self.assertFalse(result)

        success = self.client.login(username="jeff", otp="123456")
        self.assertTrue(success)
