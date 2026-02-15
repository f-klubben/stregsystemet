from sso.models import MemberSSO

class PasswordlessMemberBackend:
    """
    Minimal passwordless authentication backend.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            return None

        if password is not None:
            print("Password specified, not correct backend")
            return None

        try:
            return MemberSSO.objects.get(username=username)
        except MemberSSO.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return MemberSSO.objects.get(pk=user_id)
        except MemberSSO.DoesNotExist:
            return None
