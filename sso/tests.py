from django.test import TestCase
from django.urls import reverse

from sso.auth_backends import PasswordlessMemberBackend
from sso.models import MemberOTPRequest
from stregsystem.models import Member


class BaseLoginTestCase(TestCase):
    def setUp(self):
        self.member = Member.objects.create(
            pk=1,
            username="jeff",
            firstname="jeff",
            lastname="jefferson",
            gender="M",
            email="jeff@example.com",
        )
        self.login_url = reverse("sso_login")

    def tearDown(self):
        MemberOTPRequest.objects.all().delete()

    def _post_stage1(self, username, next_url="/"):
        return self.client.post(
            self.login_url,
            {
                "stage": "1",
                "username": username,
                "next": next_url,
            },
        )

    def _post_stage2(self, username, otp, next_url="/"):
        return self.client.post(
            self.login_url,
            {
                "stage": "2",
                "username": username,
                "otp_combined": f"F{otp}",
                "next": next_url,
            },
        )


class Stage1ViewTests(BaseLoginTestCase):

    def test_get_renders_stage1(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["stage"], 1)

    def test_get_preserves_next_in_context(self):
        response = self.client.get(self.login_url + "?next=/dashboard/")
        self.assertEqual(response.context["next"], "/dashboard/")

    def test_empty_username_returns_error(self):
        response = self._post_stage1("")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["stage"], 1)
        messages = [m.message for m in response.context["messages"]]
        self.assertTrue(any("username" in m.lower() for m in messages))

    def test_unknown_username_returns_error(self):
        response = self._post_stage1("ghost")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["stage"], 1)
        messages = [m.message for m in response.context["messages"]]
        self.assertTrue(any("no account" in m.lower() for m in messages))

    def test_known_username_advances_to_stage2(self):
        response = self._post_stage1("jeff")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["stage"], 2)

    def test_known_username_creates_otp_request(self):
        self._post_stage1("jeff")
        self.assertEqual(MemberOTPRequest.objects.filter(member=self.member, is_valid=True).count(), 1)

    def test_repeated_stage1_invalidates_previous_otp(self):
        self._post_stage1("jeff")
        self._post_stage1("jeff")
        self.assertEqual(MemberOTPRequest.objects.filter(member=self.member, is_valid=True).count(), 1)
        self.assertEqual(MemberOTPRequest.objects.filter(member=self.member, is_valid=False).count(), 1)

    def test_member_without_email_returns_error(self):
        self.member.email = ""
        self.member.save()
        response = self._post_stage1("jeff")
        self.assertEqual(response.context["stage"], 1)
        messages = [m.message for m in response.context["messages"]]
        self.assertTrue(any("email" in m.lower() for m in messages))

    def test_masked_email_in_context_on_stage2(self):
        response = self._post_stage1("jeff")
        self.assertIn("masked_email", response.context)
        self.assertNotIn("jeff@example.com", response.context["masked_email"])


class Stage2ViewTests(BaseLoginTestCase):

    def setUp(self):
        super().setUp()
        # Put the member through stage 1 so a valid OTP exists
        self._post_stage1("jeff")
        self.otp = MemberOTPRequest.objects.get(member=self.member, is_valid=True).code

    def test_correct_otp_redirects(self):
        response = self._post_stage2("jeff", self.otp, next_url="/dashboard/")
        self.assertRedirects(response, "/dashboard/", fetch_redirect_response=False)

    def test_correct_otp_logs_user_in(self):
        self._post_stage2("jeff", self.otp)
        self.assertTrue(self.client.session.get("_auth_user_id"))

    def test_correct_otp_consumes_request(self):
        self._post_stage2("jeff", self.otp)
        self.assertEqual(MemberOTPRequest.objects.filter(member=self.member, is_valid=True).count(), 0)

    def test_wrong_otp_stays_on_stage2(self):
        response = self._post_stage2("jeff", "99999")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["stage"], 2)

    def test_wrong_otp_does_not_log_in(self):
        self._post_stage2("jeff", "99999")
        self.assertFalse(self.client.session.get("_auth_user_id"))

    def test_wrong_otp_increments_failed_attempts(self):
        self._post_stage2("jeff", "99999")
        otp_req = MemberOTPRequest.objects.get(member=self.member, is_valid=True)
        self.assertEqual(otp_req.failed_attempts, 1)

    def test_max_attempts_issues_new_otp(self):
        for _ in range(PasswordlessMemberBackend.MAX_OTP_ATTEMPTS):
            self._post_stage2("jeff", "99999")
        # Original OTP should be invalidated; a fresh one issued
        self.assertEqual(MemberOTPRequest.objects.filter(member=self.member, is_valid=True).count(), 1)
        fresh = MemberOTPRequest.objects.get(member=self.member, is_valid=True)
        self.assertNotEqual(fresh.code, self.otp)

    # def test_max_attempts_shows_resend_message(self):
    #    for _ in range(PasswordlessMemberBackend.MAX_OTP_ATTEMPTS):
    #        self._post_stage2("jeff", "99999")
    #    response = self._post_stage2("jeff", "99999")
    #    messages = [m.message for m in response.context["messages"]]
    #    self.assertTrue(any("new code" in m.lower() for m in messages))

    def test_unknown_username_in_stage2_restarts(self):
        response = self._post_stage2("ghost", self.otp)
        self.assertRedirects(response, self.login_url, fetch_redirect_response=False)

    def test_otp_combined_field_parsed_correctly(self):
        """F prefix is stripped; backend receives only the 5 digits."""
        response = self._post_stage2("jeff", self.otp)
        self.assertRedirects(response, "/", fetch_redirect_response=False)

    def test_individual_cell_fields_accepted_as_fallback(self):
        """Individual otp_1...otp_5 fields work when otp_combined is absent."""
        digits = list(self.otp)
        response = self.client.post(
            self.login_url,
            {
                "stage": "2",
                "username": "jeff",
                "next": "/",
                **{f"otp_{i+1}": d for i, d in enumerate(digits)},
            },
        )
        self.assertRedirects(response, "/", fetch_redirect_response=False)


class ResendOTPViewTests(BaseLoginTestCase):
    def setUp(self):
        super().setUp()
        self._post_stage1("jeff")
        self.original_otp = MemberOTPRequest.objects.get(member=self.member, is_valid=True).code
        self.resend_url = reverse("sso_resend_otp")

    def _resend(self, username="jeff", next_url="/"):
        return self.client.post(self.resend_url, {"username": username, "next": next_url})

    def test_resend_invalidates_old_otp(self):
        self._resend()
        self.assertEqual(MemberOTPRequest.objects.filter(member=self.member, is_valid=True).count(), 1)
        self.assertEqual(MemberOTPRequest.objects.filter(code=self.original_otp, is_valid=True).count(), 0)

    def test_resend_creates_new_otp(self):
        self._resend()
        new_otp = MemberOTPRequest.objects.get(member=self.member, is_valid=True).code
        self.assertNotEqual(new_otp, self.original_otp)

    def test_resend_returns_stage2(self):
        response = self._resend()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["stage"], 2)

    def test_resend_unknown_username_redirects_to_login(self):
        response = self._resend(username="ghost")
        self.assertRedirects(response, self.login_url, fetch_redirect_response=False)

    def test_new_otp_is_accepted_after_resend(self):
        self._resend()
        new_otp = MemberOTPRequest.objects.get(member=self.member, is_valid=True).code
        response = self._post_stage2("jeff", new_otp)
        self.assertRedirects(response, "/", fetch_redirect_response=False)

    def test_old_otp_rejected_after_resend(self):
        self._resend()
        response = self._post_stage2("jeff", self.original_otp)
        self.assertFalse(self.client.session.get("_auth_user_id"))


class PasswordlessMemberBackendTests(BaseLoginTestCase):
    """
    Tests for the auth backend in isolation, called directly rather than
    through the view, to verify its contract independently.
    """

    def setUp(self):
        super().setUp()
        self.backend = PasswordlessMemberBackend()

    def _authenticate(self, username, otp):
        return self.backend.authenticate(None, username=username, otp=otp)

    def test_generate_companion_user_twice(self):
        self.member.generate_companion_user()

        self.member.paired_user = None
        self.member.generate_companion_user()

    def test_generated_companion_user_unique(self):
        self.member.generate_companion_user()
        new_user = self.member.paired_user

        self.member.paired_user = None
        self.member.generate_companion_user()

        # Check that the newly generated user actually is new.
        self.assertNotEquals(self.member.paired_user, new_user)

    def test_correct_otp_returns_user(self):
        MemberOTPRequest.objects.create(member=self.member, code="12345")
        user = self._authenticate("jeff", "12345")
        self.assertIsNotNone(user)

    def test_wrong_otp_returns_none(self):
        MemberOTPRequest.objects.create(member=self.member, code="12345")
        user = self._authenticate("jeff", "99999")
        self.assertIsNone(user)

    def test_no_otp_request_returns_none(self):
        user = self._authenticate("jeff", "12345")
        self.assertIsNone(user)

    def test_invalid_otp_request_returns_none(self):
        MemberOTPRequest.objects.create(member=self.member, code="12345", is_valid=False)
        user = self._authenticate("jeff", "12345")
        self.assertIsNone(user)

    def test_unknown_username_returns_none(self):
        user = self._authenticate("ghost", "12345")
        self.assertIsNone(user)

    def test_correct_otp_consumes_request(self):
        MemberOTPRequest.objects.create(member=self.member, code="12345")
        self._authenticate("jeff", "12345")
        self.assertEqual(MemberOTPRequest.objects.filter(member=self.member, is_valid=True).count(), 0)

    def test_wrong_otp_increments_failed_attempts(self):
        req = MemberOTPRequest.objects.create(member=self.member, code="12345")
        self._authenticate("jeff", "99999")
        req.refresh_from_db()
        self.assertEqual(req.failed_attempts, 1)

    def test_exceeded_attempts_returns_none_for_correct_otp(self):
        req = MemberOTPRequest.objects.create(
            member=self.member,
            code="12345",
            failed_attempts=PasswordlessMemberBackend.MAX_OTP_ATTEMPTS,
        )
        user = self._authenticate("jeff", "12345")
        self.assertIsNone(user)

    def test_within_attempt_limit_accepts_correct_otp(self):
        # MAX - 1 failures should still allow the correct code through
        req = MemberOTPRequest.objects.create(
            member=self.member,
            code="12345",
            failed_attempts=PasswordlessMemberBackend.MAX_OTP_ATTEMPTS - 1,
        )
        user = self._authenticate("jeff", "12345")
        self.assertIsNotNone(user)

    def test_missing_username_returns_none(self):
        user = self.backend.authenticate(None, username=None, otp="12345")
        self.assertIsNone(user)

    def test_missing_otp_returns_none(self):
        user = self.backend.authenticate(None, username="jeff", otp=None)
        self.assertIsNone(user)

    def test_get_user_returns_paired_user(self):
        MemberOTPRequest.objects.create(member=self.member, code="12345")
        user = self._authenticate("jeff", "12345")
        fetched = self.backend.get_user(user.pk)
        self.assertEqual(fetched, user)

    def test_get_user_missing_returns_none(self):
        result = self.backend.get_user(99999)
        self.assertIsNone(result)
