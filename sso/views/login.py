import random
import string
from typing import Optional
from urllib.parse import urlparse, parse_qs
from oauth2_provider.models import Application

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
    send_fcode_mail(member, full_code, f"hffps://{otp}", "linky")


def _get_client_from_next(next_url: str) -> Optional[Application]:
    parsed = urlparse(next_url)
    params = parse_qs(parsed.query)
    client_id = params.get("client_id", [None])[0]

    if not client_id:
        return None

    try:
        return Application.objects.get(client_id=client_id)
    except Application.DoesNotExist:
        return None


class CustomLoginView(View):
    template_name = "sso/login.html"

    def _base_context(self, request) -> dict:
        next_url = request.GET.get("next") or request.POST.get("next", "/")
        if next_url == "":
            service_name = _get_client_from_next(next_url).name
        else:
            service_name = None

        return {
            "next": next_url,
            "service_name": service_name,
        }

    def get(self, request):
        ctx = self._base_context(request)
        ctx["stage"] = 1
        return render(request, self.template_name, ctx)

    def post(self, request):
        stage = request.POST.get("stage", "1")
        if stage == "1":
            return self._handle_stage_1(request)
        if stage == "2":
            return self._handle_stage_2(request)
        # Something has gone wrong, restart
        return redirect("sso_login")

    def _handle_stage_1(self, request):
        ctx = self._base_context(request)
        username = request.POST.get("username", "").strip()
        ctx.update(stage=1, username=username)

        if not username:
            messages.error(request, "Indtast dit brugernavn")
            return render(request, self.template_name, ctx)

        try:
            member = Member.objects.get(username=username)
        except Member.DoesNotExist:
            messages.error(request, "Der findes ingen stregbruger med det navn")
            return render(request, self.template_name, ctx)

        if not member.email:
            messages.error(request, "Din stregbruger har ingen mailadresse. Kontakt TREO'en på treo@fklub.dk for hjælp")
            return render(request, self.template_name, ctx)

        otp = _issue_otp(member)
        _send_otp_email(member, otp)

        ctx.update(
            stage=2,
            masked_email=_mask_email(member.email),
        )
        messages.info(request, "En F-kode er blevet sendt til din mailadresse")
        return render(request, self.template_name, ctx)

    def _handle_stage_2(self, request):
        ctx = self._base_context(request)
        username = request.POST.get("username", "").strip()
        next_url = ctx["next"]
        ctx.update(stage=2, username=username)

        try:
            member = Member.objects.get(username=username)
            ctx["masked_email"] = _mask_email(member.email)
        except Member.DoesNotExist:
            # Something has gone wrong, restart
            return redirect("sso_login")

        otp = self._extract_otp_digits(request)

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
            return render(request, self.template_name, ctx)

        login(request, user, backend="sso.auth_backends.PasswordlessMemberBackend")
        return redirect(next_url or "index")

    @staticmethod
    def _extract_otp_digits(request) -> str:
        """
        Prefer the hidden combined field ('F' + 5 digits).
        Fall back to reading the five individual cell fields otp_1 … otp_5.
        Returns the 5 numeric digits only (without the leading 'F').
        """
        combined = request.POST.get("otp_combined", "")
        if combined.startswith("F") and len(combined) == 6:
            return combined[1:]
        return "".join(request.POST.get(f"otp_{i}", "") for i in range(1, 6))


class ResendOTPView(View):
    template_name = "modal/login.html"

    def post(self, request):
        username = request.POST.get("username", "").strip()
        next_url = request.POST.get("next", "/")

        try:
            member = Member.objects.get(username=username)
        except Member.DoesNotExist:
            return redirect("sso_login")

        otp = _issue_otp(member)
        _send_otp_email(member, otp)

        messages.info(request, "Vi har sendt en ny F-kode til din mailadresse")
        ctx = {
            "stage": 2,
            "username": username,
            "next": next_url,
            "masked_email": _mask_email(member.email),
            "service_name": request.session.get("sso_service_name", ""),
        }
        return render(request, self.template_name, ctx)
