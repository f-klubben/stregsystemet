from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^$', views.kiosk),
    re_path(r'^random$', views.find_random_media),
    re_path(r'^next_real/(?P<item_id>\d+)/$', views.find_next_media_real),
]
