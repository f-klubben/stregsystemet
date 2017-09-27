import datetime
from django.db.models import Q, F, Count, Case, When


def make_active_productlist_query(queryset):
    now = datetime.datetime.now()
    a = (
        queryset.annotate(b=Count(Case(
            When(start_date=None, then=1),
            When(sale__timestamp__gt=F("start_date"), then=1),
            default=None
        ))).filter(
            Q(active=True)
            & ((Q(deactivate_date=None) | Q(deactivate_date__gte=now)))
            & (Q(start_date=None) | Q(quantity__gt=F("b"))))
    )
    return a


def make_inactive_productlist_query(queryset):
    now = datetime.datetime.now()
    a = (
        queryset.annotate(b=Count(Case(
            When(start_date=None, then=1),
            When(sale__timestamp__gt=F("start_date"), then=1),
            default=None
        ))).exclude(
            Q(active=True)
            & ((Q(deactivate_date=None) | Q(deactivate_date__gte=now)))
            & (Q(start_date=None) | Q(quantity__gt=F("b"))))
    )
    return a


def make_room_specific_query(room):
    return (
        Q(rooms__id=room) | Q(rooms=None)
    )
