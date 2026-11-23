from django.contrib.auth.mixins import LoginRequiredMixin
from oauth2_provider.views.base import AuthorizationView


class CustomOAuth2ProviderLoginView(AuthorizationView, LoginRequiredMixin):
    """
    Override login_url as used in authorization view.
    """

    login_url = "/ffo/login/"
