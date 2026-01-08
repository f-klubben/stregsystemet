import json

from datetime import datetime
from django.utils import timezone
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
    item = (
        KioskItem.objects.filter(active=True)
        .filter(
            (Q(start_datetime__isnull=True) | Q(start_datetime__lte=timezone.now()))
            & (Q(end_datetime__isnull=True) | Q(end_datetime__gte=timezone.now()))
        )
        .order_by('?')
        .first()
    )
    if item is None:
        raise Http404("No active kiosk items found")

    media_url = item.media.url if item.media else item.website_url
    is_image = item.is_image if item.media else False

    response_data = {
        "id": item.id,
        "url": media_url,
        "is_image": is_image,
        "has_media": item.has_media,
        "duration": item.duration,
    }
    return HttpResponse(json.dumps(response_data), content_type="application/json")


def find_next_media_real(request, item_id):
    item = KioskItem.objects.get(pk=item_id)

    item_count = (
        KioskItem.objects.filter(active=True)
        .filter(
            (Q(start_datetime__isnull=True) | Q(start_datetime__lte=timezone.now()))
            & (Q(end_datetime__isnull=True) | Q(end_datetime__gte=timezone.now()))
        )
        .count()
    )
    if item_count == 0:
        raise Http404("No active kiosk items found")

    # Get the item at the index, trust that Django does this smartly.
    try:
        next_item = (
            KioskItem.objects.filter(active=True)
            .filter(
                (Q(start_datetime__isnull=True) | Q(start_datetime__lte=timezone.now()))
                & (Q(end_datetime__isnull=True) | Q(end_datetime__gte=timezone.now()))
            )
            .order_by('ordering', 'id')
            .filter(Q(ordering__gt=item.ordering) | (Q(ordering=item.ordering) & Q(id__gt=item.id)))[0]
        )
    except IndexError:
        next_item = (
            KioskItem.objects.filter(active=True)
            .filter(
                (Q(start_datetime__isnull=True) | Q(start_datetime__lte=timezone.now()))
                & (Q(end_datetime__isnull=True) | Q(end_datetime__gte=timezone.now()))
            )
            .order_by('ordering', 'id')[0]
        )

    media_url = next_item.media.url if next_item.media else next_item.website_url
    is_image = next_item.is_image if next_item.media else False

    response_data = {
        "id": next_item.id,
        "url": media_url,
        "is_image": is_image,
        "has_media": next_item.has_media,
        "duration": next_item.duration,
    }
    return HttpResponse(json.dumps(response_data), content_type="application/json")
