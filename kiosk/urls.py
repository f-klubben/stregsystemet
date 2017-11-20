from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.kiosk),
    url(r'^random$', views.find_random_image),
    url(r'^next_real/(?P<item_id>\d+)/$', views.find_next_image_real),
    url(r'^item/(?P<item_id>\d+)/$', views.renderItem),
]
