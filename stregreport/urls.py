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

from . import views

urlpatterns = [
    url(r'^admin/stregsystem/razzia/bread/$', views.bread),
    url(r'^admin/stregsystem/report/sales/$', views.sales),
    url(r'^admin/stregsystem/report/ranks/$', views.ranks),
    url(r'^admin/stregsystem/report/daily/$', views.daily),
    url(r'^admin/stregsystem/report/ranks/(?P<year>\d+)$', views.ranks),
    url(r'^admin/stregsystem/report/$', views.reports),
    url(r'^admin/stregsystem/report/sales_api$', views.sales_api),
]
