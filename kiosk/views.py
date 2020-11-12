import json

from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import render

from .models import KioskItem


def kiosk(request):
    return render(request, 'kiosk.html', locals())


def find_random_media(request):
    """
    Randomly get a media and return the relative url
    """
    item = KioskItem.objects.filter(active=True).order_by('?').first()
    if item is None:
        raise Http404("No active kiosk items found")

    response_data = {
        "id": item.id,
        "url": item.media.url,
        "is_image": item.is_image,
    }
    return HttpResponse(
        json.dumps(response_data),
        content_type="application/json"
    )


def find_next_media_real(request, item_id):
    item = KioskItem.objects.get(pk=item_id)

    item_count = KioskItem.objects.filter(active=True).count()
    if item_count == 0:
        raise Http404("No active kiosk items found")

    # Get the item at the index, trust that Django does this smartly.
    try:
        next_item = (
            KioskItem.objects
            .filter(active=True)
            .order_by('ordering', 'id')
            .filter(
                Q(ordering__gt=item.ordering)
                | (Q(ordering=item.ordering) & Q(id__gt=item.id))
            )[0]
        )
    except IndexError:
        next_item = (
            KioskItem.objects
            .filter(active=True)
            .order_by('ordering', 'id')[0]
        )
    response_data = {
        "id": next_item.id,
        "url": next_item.media.url,
        "is_image": next_item.is_image,
    }
    return HttpResponse(
        json.dumps(response_data),
        content_type="application/json"
    )
