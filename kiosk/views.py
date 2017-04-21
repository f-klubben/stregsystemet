from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect

from models import KioskItem

def show_pics(request):
    items = list(KioskItem.objects.all())
    return render(request, 'allkioskitems.html', locals())

def kiosk(request):
    return render(request, 'kiosk.html', locals())

def find_random_image(request):
    item = KioskItem.objects.filter(active=True).order_by('?').first()
    return HttpResponse(item.image.url, content_type="text/plain")

