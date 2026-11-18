from oauth2_provider.oauth2_validators import OAuth2Validator


class StregsystemOAuth2Validator(OAuth2Validator):
    # Claims are only emitted when the mapped scope was granted.
    oidc_claim_scope = OAuth2Validator.oidc_claim_scope | {
        "groups": "groups",
        "username": "profile",
    }

    def get_additional_claims(self):
        return {
            "groups": lambda request: list(request.user.groups.order_by("name").values_list("name", flat=True)),
            "username": lambda request: self._member_username(request.user),
            "name": lambda request: self._member_name(request.user),
        }

    @staticmethod
    def _member(user):
        """The Member a companion user was created for, see Member.generate_companion_user."""
        if user is None or not user.is_authenticated:
            return None
        return user.member_set.order_by("pk").first()

    @classmethod
    def _member_username(cls, user):
        member = cls._member(user)
        return member.username if member is not None else None

    @classmethod
    def _member_name(cls, user):
        member = cls._member(user)
        if member is None:
            return None
        return f"{member.firstname} {member.lastname}".strip()
