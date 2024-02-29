"""stregsystem URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/ref/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  re_path(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  re_path(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  re_path(r'^blog/', include('blog.urls'))
"""
from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^admin/stregsystem/report/sales/$', views.sales, name="salesreporting"),
    re_path(r'^admin/stregsystem/report/ranks/$', views.ranks),
    re_path(r'^admin/stregsystem/report/daily/$', views.daily),
    re_path(r'^admin/stregsystem/report/ranks/(?P<year>\d+)$', views.ranks),
    re_path(r'^admin/stregsystem/report/$', views.reports),
    re_path(r'^admin/stregsystem/report/sales_api$', views.sales_api),
    re_path(r'^admin/stregsystem/report/categories/$', views.user_purchases_in_categories),
]
