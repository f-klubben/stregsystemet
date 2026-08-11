from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views import View
from django.conf import settings

from sso.auth_backends import PasswordlessMemberBackend
from sso.models import MemberOTPRequest
from sso.mail import send_fcode_mail
from stregsystem.models import Member


def _issue_otp(member: Member) -> str:
    MemberOTPRequest.objects.filter(member=member).update(is_valid=False)
    otp = MemberOTPRequest.generate_otp_code()
    MemberOTPRequest.objects.create(member=member, code=otp)
    return otp


def _send_otp_email(member: Member, otp: str, redirect_url: str) -> None:
    full_code = f"F-{otp}"
    print(f"Sent F-code: {full_code}")
    send_fcode_mail(member, full_code, redirect_url)


class CustomLoginView(View):
    template_name = "modal/login.html"

    def get(self, request):
        stage = 1
        next = request.GET.get("next") or request.POST.get("next", "/")
        messages.info(request, "Log ind for at fortsætte")
        return render(request, self.template_name, locals())

    def post(self, request):
        stage = int(request.POST.get("stage", "1"))
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

        masked_email = member.masked_email
        otp_ttl = settings.SSO_CODE_DURATION_MIN * 60
        otp_digits = range(1, MemberOTPRequest.OTP_DIGITS + 1)

        if stage == 1:  # Generate and send OTP
            otp = _issue_otp(member)
            _send_otp_email(member, otp, next)

            stage = 2
            messages.info(request, "En F-kode er blevet sendt til din mailadresse")
            return render(request, self.template_name, locals())

        if stage == 2:  # Try to validate OTP
            otp = request.POST.get("otp", "")

            user = authenticate(request, username=username, otp=otp)

            if user is None:
                otp_request = (
                    MemberOTPRequest.objects.filter(member=member, is_valid=True).order_by("-created_at").first()
                )

                if otp_request is None or otp_request.failed_attempts >= settings.SSO_MAX_ATTEMPTS:
                    fresh_otp = _issue_otp(member)
                    _send_otp_email(member, fresh_otp, next)
                    messages.error(
                        request,
                        "For mange for forkerte forsøg. Vi har sendt en ny F-kode",
                    )
                else:
                    messages.error(request, "Forkert F-kode. Dobbelttjek mailen og forsøg igen")
                return render(request, self.template_name, locals())

            login(request, user, backend="sso.auth_backends.PasswordlessMemberBackend")
            return redirect(next or "index")

        # Something has gone wrong, restart
        return redirect("sso_login")
