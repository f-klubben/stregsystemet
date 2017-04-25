from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static

from . import views

urlpatterns = [
    url(r'^$', views.kiosk),
    url(r'^random$', views.find_random_image),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
