import datetime

from django.shortcuts import render

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDay
from django.forms import fields
from django.forms.widgets import SelectDateWidget
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.utils import dateparse, timezone

from razzia.models import Razzia, RazziaEntry
from stregreport.forms import CategoryReportForm
from stregsystem.models import Category, Member, Product, Sale
from stregsystem.templatetags.stregsystem_extras import money


# Create your views here.
@permission_required("stregreport.host_razzia")
def razzia(request, razzia_id):
    if request.method == 'POST':
        return razzia_view_single(request, razzia_id, request.POST['username'], razzia_type=razzia_type, title=title)
    else:
        return razzia_view_single(request, razzia_id, None, razzia_type=razzia_type, title=title)


@permission_required("stregreport.host_razzia")
def razzia_view_single(request, razzia_id, queryname, title=None):
    razzia = get_object_or_404(Razzia, pk=razzia_id)

    template = 'razzia.html'

    if queryname is None:
        return render(request, template, locals())

    result = list(Member.objects.filter(username__iexact=queryname))
    if len(result) == 0:
        return render(request, template, locals())

    member = result[0]

    entries = list(razzia.razziaentry_set.filter(member__pk=member.pk).order_by('-time'))
    turns_already = len(entries)
    turn_interval = datetime.timedelta(minutes=razzia.turn_interval)

    within_wait = True

    # Get most recent visit
    if len(entries) > 0:
        within_wait = entries[0].time > timezone.now() - turn_interval

    # Back too soon?
    if not within_wait:
        drunkard = True
        remaining_time_secs = int(((entries[0].time + turn_interval) - timezone.now()).total_seconds() % 60)
        remaining_time_mins = int(((entries[0].time + turn_interval) - timezone.now()).total_seconds() // 60)
        return render(request, template, locals())

    RazziaEntry(member=member, razzia=razzia).save()

    return render(request, template, locals())
