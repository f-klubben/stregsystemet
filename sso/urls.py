from django.urls import path

from . import views

urlpatterns = [
    path('login/', views.login.CustomLoginView.as_view(), name='sso_login'),
]
