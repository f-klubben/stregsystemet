from django.urls import path

from .views.login import CustomLoginView, ResendOTPView

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='sso_login'),
    path('login/resend/', ResendOTPView.as_view(), name='sso_resend_otp'),
]
