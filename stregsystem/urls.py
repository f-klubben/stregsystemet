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
from django.conf.urls import url
from django.contrib import admin

from . import views

# urlpatterns = [
#     url(r'^admin/', admin.site.urls),
# ]

urlpatterns = [
    url(r'^$', views.roomindex),
    url(r'^(?P<room_id>\d+)/$', views.index),
    url(r'^(?P<room_id>\d+)/sale/$', views.sale, name="sale"),
    url(r'^(?P<room_id>\d+)/sale/(?P<member_id>\d+)/$', views.menu_sale),
    url(r'^(?P<room_id>\d+)/sale/(?P<member_id>\d+)/(?P<product_id>\d+)/$', views.menu_sale),
    url(r'^(?P<room_id>\d+)/user/(?P<member_id>\d+)/$', views.menu_userinfo),

    # Uncomment for public stats
    #(r'^ranks/(?P<year>\d+)/$', 'ranks'),
    #(r'^ranks/$', 'ranks'),

    #(r'^admin/', 'admin'),
]

# urlpatterns += patterns('',
#     (r'^mat/$', 'django.views.generic.simple.redirect_to', {'url': '/3/'}),
#     (r'^cs/$', 'django.views.generic.simple.redirect_to', {'url': '/2/'}),
# )
