from datetime import timedelta

from django.contrib.auth.models import User
from django.utils import timezone

from sso.models import MemberOTPRequest
from stregsystem.models import Member


class PasswordlessMemberBackend:
    """
    Minimal passwordless authentication backend.
    """

    MAX_RETRIES_SAME_OTP = 3
    OTP_DURATION_MIN = 5

    def authenticate(self, request, username=None, password=None, otp=None, **kwargs):
        if username is None:
            return None

        # No password provided for this backend
        if password is not None:
            return None

        try:
            member = Member.objects.get(username=username)
        except Member.DoesNotExist:
            return None

        cutoff = timezone.now() - timedelta(minutes=self.OTP_DURATION_MIN)

        # If no OTP or only old OTP, send new OTP
        previous_otp_requests = MemberOTPRequest.objects.filter(member=member).order_by('created_at')
        if previous_otp_requests.count() == 0 or previous_otp_requests.first().created_at < cutoff:
            self.request_otp(member)
            return None

        most_recent_otp = previous_otp_requests.first()

        # Too many tries for this OTP
        if previous_otp_requests.filter(code=most_recent_otp.code).count() >= self.MAX_RETRIES_SAME_OTP:
            self.request_otp(member)
            return None

        # Test whether correct OTP provided
        if not self.compare_otp(most_recent_otp.code, otp):
            # Log failed attempt
            MemberOTPRequest.objects.create(code=most_recent_otp.code, member=member)
            return None

        # Login successful - Clear login attempts
        MemberOTPRequest.objects.filter(member=member).delete()

        if member.paired_user is None:
            member.generate_companion_user()

        return member.paired_user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    def request_otp(self, member: Member):
        MemberOTPRequest.objects.create(code=self.generate_otp(), member=member)

    def compare_otp(self, target_otp, guess_otp) -> bool:
        return target_otp == guess_otp

    def generate_otp(self):
        return "123456"
