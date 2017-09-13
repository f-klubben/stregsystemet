import pprint
import time
from datetime import datetime

from django.http import Http404
from django.http import HttpResponse
from django.shortcuts import render

from .models import KioskItem


def kiosk(request):
    return render(request, 'kiosk.html', locals())


def find_random_image(request):
    """
    Randomly get an image and return the relative url
    """
    item = KioskItem.objects.filter(active=True).order_by('?').first()
    if item is None:
        raise Http404("No active kiosk items found")

    return HttpResponse(item.image.url, content_type="text/plain")


def find_next_image(request):
    """
    Deterministically return an image for the kiosk screen.
    This ensures that each kiosk item will be displayed an equal amount of time,
    assuming the screen call this method semi-frequently.

    :param request: Django request obj
    :return: The request or 404 if no active kiosk items was found.
    """
    item_count = KioskItem.objects.filter(active=True).count()
    if item_count == 0:
        raise Http404("No active kiosk items found")

    # The duration for each item
    # TODO: Make this a variable for someone to adjust (Where?)
    duration = 10
    # The total cycle time
    complete_cycle_time = duration * item_count
    # Get a unit timestamp
    seconds_since_epoch = time.mktime(datetime.now().timetuple())
    # Find the next index, by getting a number in the range [0;complete_cycle_time[
    # and divide it by the duration of each
    next_index = int((seconds_since_epoch % complete_cycle_time) / duration)
    # Get the item at the index, trust that Django does this smartly.
    next_item = KioskItem.objects.filter(active=True).order_by('name')[next_index]
    return HttpResponse(next_item.image.url, content_type="text/plain")
