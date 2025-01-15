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
from .models import BreadRazzia

urlpatterns = [
    re_path(r'^admin/stregsystem/razzia/bread/(?P<razzia_id>\d+)/$', views.razzia, {'razzia_type' : BreadRazzia.BREAD, 'title': 'Brødrazzia'}, name="bread_view"),
    re_path(r'^admin/stregsystem/razzia/foobar/(?P<razzia_id>\d+)/$', views.razzia, {'razzia_type' : BreadRazzia.FOOBAR, 'title': 'Foobar razzia'}, name="foobar_view"),
    re_path(r'^admin/stregsystem/razzia/fnugfald/(?P<razzia_id>\d+)/$', views.razzia, {'razzia_type' : BreadRazzia.FNUGFALD, 'title': 'Fnugfald razzia'}, name="fnugfald_view"),
    re_path(r'^admin/stregsystem/razzia/bread/(?P<razzia_id>\d+)/members$', views.razzia_members, {'razzia_type' : BreadRazzia.BREAD, 'title': 'Brødrazzia'}),
    re_path(r'^admin/stregsystem/razzia/foobar/(?P<razzia_id>\d+)/members$', views.razzia_members, {'razzia_type' : BreadRazzia.FOOBAR, 'title': 'Foobar razzia'}),
    re_path(r'^admin/stregsystem/razzia/fnugfald/(?P<razzia_id>\d+)/members$', views.razzia_members, {'razzia_type' : BreadRazzia.FNUGFALD, 'title': 'Fnugfald razzia'}),
    re_path(r'^admin/stregsystem/razzia/bread/$', views.razzia_menu, {'razzia_type' : BreadRazzia.BREAD, 'new_text': "New bread razzia", 'title': 'Brødrazzia'}),
    re_path(r'^admin/stregsystem/razzia/foobar/$', views.razzia_menu, {'razzia_type' : BreadRazzia.FOOBAR, 'new_text': "New foobar razzia", 'title': 'Foobar razzia'}),
    re_path(r'^admin/stregsystem/razzia/fnugfald/$', views.razzia_menu, {'razzia_type' : BreadRazzia.FNUGFALD, 'new_text': "New fnugfald razzia", 'title': 'Fnugfald razzia'}),
    re_path(r'^admin/stregsystem/razzia/bread/new$', views.new_razzia, {'razzia_type' : BreadRazzia.BREAD}, name="razzia_new_BR"),
    re_path(r'^admin/stregsystem/razzia/foobar/new$', views.new_razzia, {'razzia_type' : BreadRazzia.FOOBAR}, name="razzia_new_FB"),
    re_path(r'^admin/stregsystem/razzia/fnugfald/new$', views.new_razzia, {'razzia_type' : BreadRazzia.FNUGFALD}, name="razzia_new_FF"),
    re_path(r'^admin/stregsystem/razzia/wizard_guide/$', views.razzia_wizard),
    re_path(r'^admin/stregsystem/razzia/wizard/$', views.razzia_view, name="razzia_view"),
    re_path(r'^admin/stregsystem/report/sales/$', views.sales, name="salesreporting"),
    re_path(r'^admin/stregsystem/report/ranks/$', views.ranks, name="report_categoryranks"),
    re_path(r'^admin/stregsystem/report/daily/$', views.daily),
    re_path(r'^admin/stregsystem/report/ranks/(?P<year>\d+)$', views.ranks),
    re_path(r'^admin/stregsystem/report/$', views.reports),
    re_path(r'^admin/stregsystem/report/sales_api$', views.sales_api),
    re_path(r'^admin/stregsystem/report/categories/$', views.user_purchases_in_categories),
]
