from django.urls import path

from .views.login import CustomLoginView

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='sso_login'),
]
