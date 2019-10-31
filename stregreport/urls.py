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
from .models import BreadRazzia

urlpatterns = [
    url(r'^admin/stregsystem/razzia/bread/(?P<razzia_id>\d+)/$', views.razzia, {'razzia_type' : BreadRazzia.BREAD, 'title': 'Brødrazzia'}, name="bread_view"),
    url(r'^admin/stregsystem/razzia/foobar/(?P<razzia_id>\d+)/$', views.razzia, {'razzia_type' : BreadRazzia.FOOBAR, 'title': 'Foobar razzia'}, name="foobar_view"),
    url(r'^admin/stregsystem/razzia/bread/(?P<razzia_id>\d+)/members$', views.razzia_members, {'razzia_type' : BreadRazzia.BREAD, 'title': 'Brødrazzia'}),
    url(r'^admin/stregsystem/razzia/foobar/(?P<razzia_id>\d+)/members$', views.razzia_members, {'razzia_type' : BreadRazzia.FOOBAR, 'title': 'Foobar razzia'}),
    url(r'^admin/stregsystem/razzia/bread/$', views.razzia_menu, {'razzia_type' : BreadRazzia.BREAD, 'new_text': "New bread razzia", 'title': 'Brødrazzia'}),
    url(r'^admin/stregsystem/razzia/foobar/$', views.razzia_menu, {'razzia_type' : BreadRazzia.FOOBAR, 'new_text': "New foobar razzia", 'title': 'Foobar razzia'}),
    url(r'^admin/stregsystem/razzia/bread/new$', views.new_razzia, {'razzia_type' : BreadRazzia.BREAD}, name="razzia_new_BR"),
    url(r'^admin/stregsystem/razzia/foobar/new$', views.new_razzia, {'razzia_type' : BreadRazzia.FOOBAR}, name="razzia_new_FB"),
    url(r'^admin/stregsystem/razzia/wizard_guide/$', views.razzia_wizard),
    url(r'^admin/stregsystem/razzia/wizard/$', views.razzia_view, name="razzia_view"),
    url(r'^admin/stregsystem/report/sales/$', views.sales, name="salesreporting"),
    url(r'^admin/stregsystem/report/ranks/$', views.ranks),
    url(r'^admin/stregsystem/report/daily/$', views.daily),
    url(r'^admin/stregsystem/report/ranks/(?P<year>\d+)$', views.ranks),
    url(r'^admin/stregsystem/report/$', views.reports),
    url(r'^admin/stregsystem/report/sales_api$', views.sales_api),
    url(r'^admin/stregsystem/report/categories/$', views.user_purchases_in_categories),
]
