from datetime import timedelta

from django.contrib.auth.models import User
from django.utils import timezone

from sso.models import MemberOTPRequest
from stregsystem.models import Member


class PasswordlessMemberBackend:
    """
    Minimal passwordless authentication backend.
    """

    MAX_OTP_ATTEMPTS = 3
    OTP_DURATION_MIN = 5

    def authenticate(self, request, username=None, otp=None, **kwargs):
        if username is None or not otp:
            return None

        try:
            member = Member.objects.get(username=username)
        except Member.DoesNotExist:
            return None

        otp_request = MemberOTPRequest.objects.filter(member=member, is_valid=True).order_by("-created_at").first()
        if not otp_request:
            return None

        # Too old request
        if otp_request.created_at < timezone.now() - timedelta(minutes=self.OTP_DURATION_MIN):
            otp_request.is_valid = False
            otp_request.save()
            return None

        # Too many tries for this OTP
        if otp_request.failed_attempts >= self.MAX_OTP_ATTEMPTS:
            otp_request.is_valid = False
            otp_request.save()
            return None

        # Test whether correct OTP provided
        if otp_request.code != otp:
            otp_request.failed_attempts += 1
            otp_request.save()
            return None

        # Login successful - Clear login attempts
        otp_request.is_valid = False
        otp_request.save()

        if member.paired_user is None:
            member.generate_companion_user()

        return member.paired_user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
