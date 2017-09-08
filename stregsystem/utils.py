import datetime
from django.db.models import Q


def make_active_productlist_query():
    now = datetime.datetime.now()
    return (
        Q(active=True)
        & (Q(deactivate_date=None) | Q(deactivate_date__gte=now))
    )
