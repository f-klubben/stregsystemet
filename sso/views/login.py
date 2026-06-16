import random
import string
from typing import Optional
from urllib.parse import urlparse, parse_qs

from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views import View

from sso.auth_backends import PasswordlessMemberBackend
from sso.models import MemberOTPRequest
from stregsystem.models import Member
from stregsystem.mail import send_fcode_mail

OTP_TTL_SECONDS = 600
OTP_DIGITS = 5


def _mask_email(email: str) -> str:
    local, domain = email.split("@", 1)
    masked = local[0] + "***" if len(local) > 1 else "***"
    return f"{masked}@{domain}"


def _generate_otp() -> str:
    return "".join(random.choices(string.digits, k=OTP_DIGITS))


def _issue_otp(member: Member) -> str:
    MemberOTPRequest.objects.filter(member=member).update(is_valid=False)
    otp = _generate_otp()
    MemberOTPRequest.objects.create(member=member, code=otp)
    return otp


def _send_otp_email(member: Member, otp: str) -> None:
    full_code = f"F-{otp}"
    print(f"Send F-code: {full_code}")
    send_fcode_mail(member, full_code, "linky")


class CustomLoginView(View):
    template_name = "modal/login.html"

    def get(self, request):
        stage = 1
        next = request.GET.get("next") or request.POST.get("next", "/")
        messages.info(request, "Log ind for at fortsætte")
        return render(request, self.template_name, locals())

    def post(self, request):
        stage = request.POST.get("stage", "1")
        if stage == "1":
            return self._handle_stage_1(request)
        if stage == "2":
            return self._handle_stage_2(request)
        # Something has gone wrong, restart
        return redirect("sso_login")

    def _handle_stage_1(self, request):
        stage = 1
        next = request.GET.get("next") or request.POST.get("next", "/")
        username = request.POST.get("username", "").strip()

        if not username:
            messages.error(request, "Indtast dit brugernavn")
            return render(request, self.template_name, locals())

        try:
            member = Member.objects.get(username=username)
        except Member.DoesNotExist:
            messages.error(request, "Der findes ingen stregbruger med det navn")
            return render(request, self.template_name, locals())

        if not member.email:
            messages.error(request, "Din stregbruger har ingen mailadresse. Kontakt TREO'en på treo@fklub.dk for hjælp")
            return render(request, self.template_name, locals())

        otp = _issue_otp(member)
        _send_otp_email(member, otp)

        stage = 2
        masked_email = _mask_email(member.email)

        messages.info(request, "En F-kode er blevet sendt til din mailadresse")
        return render(request, self.template_name, locals())

    def _handle_stage_2(self, request):
        next = request.GET.get("next") or request.POST.get("next", "/")
        username = request.POST.get("username", "").strip()
        stage = 2

        try:
            member = Member.objects.get(username=username)
            masked_email = _mask_email(member.email)
        except Member.DoesNotExist:
            # Something has gone wrong, restart
            return redirect("sso_login")

        otp = request.POST.get("otp", "")

        user = authenticate(request, username=username, otp=otp)

        if user is None:
            otp_request = MemberOTPRequest.objects.filter(member=member, is_valid=True).order_by("-created_at").first()

            if otp_request is None or otp_request.failed_attempts >= PasswordlessMemberBackend.MAX_OTP_ATTEMPTS:
                fresh_otp = _issue_otp(member)
                _send_otp_email(member, fresh_otp)
                messages.error(
                    request,
                    "For mange for forkerte forsøg. Vi har sendt en ny F-kode",
                )
            else:
                messages.error(request, "Forkert F-kode. Dobbelttjek mailen og forsøg igen")
            return render(request, self.template_name, locals())

        login(request, user, backend="sso.auth_backends.PasswordlessMemberBackend")
        return redirect(next or "index")
