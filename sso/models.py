import random
import string

from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import models

from stregsystem.models import Member


class MemberOTPRequest(models.Model):
    OTP_DIGITS = 5

    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    code = models.CharField(max_length=OTP_DIGITS)  #  Only digits stored, but can start with multiple '0'
    failed_attempts = models.PositiveSmallIntegerField(default=0)
    is_valid = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def generate_otp_code(cls) -> str:
        return "".join(random.choices(string.digits, k=cls.OTP_DIGITS))
