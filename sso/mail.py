from django.conf import settings
from stregsystem.mail import send_template_mail
from stregsystem.models import Member


def send_fcode_mail(member: Member, fcode: str, redirect_url: str):
    send_template_mail(
        member,
        "send_otp.html",
        {
            **vars(member),
            'fcode': fcode,
            'redirect_url': redirect_url,
            'expire_duration': settings.SSO_CODE_DURATION_MIN,
        },
        "Stregsystem FFO",
    )
