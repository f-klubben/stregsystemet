import datetime

from django.contrib.auth.decorators import permission_required
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone

from razzia.models import Razzia, RazziaEntry
from stregsystem.models import Member


# Create your views here.
@permission_required("razzia.host_razzia")
def razzia(request, razzia_id):
    if request.method == 'POST':
        return razzia_view_single(request, razzia_id, request.POST['username'])
    else:
        return razzia_view_single(request, razzia_id, None)


@permission_required("razzia.host_razzia")
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

    timed_out = False

    # Get most recent visit
    if len(entries) > 0:
        timed_out = entries[0].time > timezone.now() - razzia.turn_interval

    # Back too soon?
    if timed_out:
        drunkard = True
        remaining_time_secs = int(((entries[0].time + razzia.turn_interval) - timezone.now()).total_seconds() % 60)
        remaining_time_mins = int(((entries[0].time + razzia.turn_interval) - timezone.now()).total_seconds() // 60)
        return render(request, template, locals())

    RazziaEntry(member=member, razzia=razzia).save()

    return render(request, template, locals())


@permission_required("razzia.browse_razzia")
def razzia_menu(request, new_text=None, title=None):
    razzias = Razzia.objects.order_by('-pk')[:3]
    return render(request, 'menu.html', locals())


@permission_required("razzia.create_razzia")
def new_razzia(request):
    razzia = Razzia(name="Foobar V2", turn_interval=datetime.timedelta(minutes=30))
    razzia.save()

    return redirect('razzia_view', razzia_id=razzia.pk)


@permission_required("razzia.view_members")
def razzia_members(request, razzia_id, title=None):
    razzia = get_object_or_404(Razzia, pk=razzia_id)
    unique_members = razzia.members.all().distinct().count()
    return render(request, 'members.html', locals())
