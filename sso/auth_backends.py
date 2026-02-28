from django.contrib.auth.models import User

from stregsystem.models import Member


class PasswordlessMemberBackend:
    """
    Minimal passwordless authentication backend.
    """

    def authenticate(self, request, username=None, password=None, otp=None, **kwargs):
        if username is None:
            return None

        if password is not None:
            print("Password specified, not correct backend")
            return None

        try:
            member = Member.objects.get(username=username)
        except Member.DoesNotExist:
            return None

        if member.paired_user is None:
            user = User.objects.create(
                username=f"sso_{member.username}",
                is_staff=False,
                is_superuser=False,
                is_active=True,
            )
            member.paired_user = user
            member.save()

        return member.paired_user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
