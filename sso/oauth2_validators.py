from oauth2_provider.oauth2_validators import OAuth2Validator


class StregsystemOAuth2Validator(OAuth2Validator):
    # Claims are only emitted when the mapped scope was granted.
    oidc_claim_scope = OAuth2Validator.oidc_claim_scope | {"groups": "groups"}

    def get_additional_claims(self):
        return {
            "groups": lambda request: list(request.user.groups.order_by("name").values_list("name", flat=True)),
        }
