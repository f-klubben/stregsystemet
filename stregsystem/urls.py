from django.conf.urls import url

from . import views
from django.shortcuts import redirect

"""stregsystem URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
urlpatterns = [
    url(r'^$', views.roomindex, name="index"),
    url(r'^admin/batch/$', views.batch_payment, name="batch"),
    url(r'^admin/mobilepaytool/$', views.mobilepaytool, name="mobilepaytool"),
    url(r'^(?P<room_id>\d+)/$', views.index, name="menu_index"),
    url(r'^(?P<room_id>\d+)/sale/$', views.sale, name="quickbuy"),
    url(r'^(?P<room_id>\d+)/sale/(?P<member_id>\d+)/$', views.menu_sale, name="menu"),
    url(r'^(?P<room_id>\d+)/sale/\d+/\d+/$', lambda request, room_id: redirect('menu_index', room_id=room_id), name="menu_sale"),
    url(r'^(?P<room_id>\d+)/user/(?P<member_id>\d+)/$', views.menu_userinfo, name="userinfo"),
    url(r'^(?P<room_id>\d+)/user/(?P<member_id>\d+)/pay$', views.menu_userpay, name="userpay"),
    url(r'^api/member/payment/qr$', views.qr_payment, name="payment_qr"),
]
