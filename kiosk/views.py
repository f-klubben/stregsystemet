from django.core.cache import caches
from django.views.decorators.cache import cache_page
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect

from models import KioskItem


def show_pics(request):
    items = list(KioskItem.objects.all())
    return render(request, 'allkioskitems.html', locals())


def kiosk(request):
    return find_random_image(request)


def clear_kiosk_cache():
    caches['kiosk'].clear()


@cache_page(5, cache='kiosk')
def find_random_image(request):
    cache = caches['kiosk']
    items = cache.get('items')

    if not items:
        items = list(KioskItem.objects.filter(active=True).order_by('?'))

    item = items.pop()
    cache.set('items', items)

    return render(request, 'kiosk.html', {'item': item})
