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
]
