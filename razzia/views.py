import datetime

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.db.models import Count
from django.forms import fields
from django.forms.widgets import SelectDateWidget
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.utils import dateparse, timezone

from razzia.models import BreadRazzia, RazziaEntry
from stregsystem.models import Member, Product


@permission_required("stregreport.host_razzia")
def razzia(request, razzia_id, razzia_type=BreadRazzia.BREAD, title=None):
    if request.method == 'POST':
        return razzia_view_single(request, razzia_id, request.POST['username'], razzia_type=razzia_type, title=title)
    else:
        return razzia_view_single(request, razzia_id, None, razzia_type=razzia_type, title=title)


@permission_required("stregreport.host_razzia")
def razzia_view_single(request, razzia_id, queryname, razzia_type=BreadRazzia.BREAD, title=None):
    razzia = get_object_or_404(BreadRazzia, pk=razzia_id, razzia_type=razzia_type)

    templates = {
        BreadRazzia.BREAD: 'bread.html',
        BreadRazzia.FOOBAR: 'foobar.html',
        BreadRazzia.FNUGFALD: 'fnugfald.html',
    }

    if queryname is None:
        return render(request, templates[razzia_type], locals())

    result = list(Member.objects.filter(username__iexact=queryname))
    if len(result) == 0:
        return render(request, templates[razzia_type], locals())

    member = result[0]

    if razzia_type == BreadRazzia.FNUGFALD:
        username = queryname
        member_name = member.firstname + " " + member.lastname
        start_date = dateparse.parse_date("2023-9-15")
        end_date = dateparse.parse_date("2023-11-4")
        product_list = [1910]
        product_dict = {k.name: 0 for k in Product.objects.filter(id__in=product_list)}
        sales_to_user = _sales_to_user_in_period(queryname, start_date, end_date, product_list, product_dict)
        items_bought = sales_to_user.items()

        try:
            item_bought_count = sales_to_user[list(sales_to_user.keys())[0]]
            if item_bought_count == 0:
                return render(request, templates[razzia_type], locals())
        except IndexError:
            return render(request, templates[razzia_type], locals())

    entries = list(razzia.razziaentry_set.filter(member__pk=member.pk).order_by('-time'))
    already_checked_in = len(entries) > 0
    wait_time = datetime.timedelta(minutes=30)
    if already_checked_in:
        last_entry = entries[0]
        within_wait = last_entry.time > timezone.now() - wait_time
    # if member has already checked in within the last hour, don't allow another check in
    if (
        already_checked_in
        and within_wait
        and (razzia_type == BreadRazzia.FOOBAR or razzia_type == BreadRazzia.FNUGFALD)
    ):
        drunkard = True
        # time until next check in is legal
        remaining_time_secs = int(((last_entry.time + wait_time) - timezone.now()).total_seconds() % 60)
        remaining_time_mins = int(((last_entry.time + wait_time) - timezone.now()).total_seconds() // 60)
    if not already_checked_in or (
        (razzia_type == BreadRazzia.FOOBAR or razzia_type == BreadRazzia.FNUGFALD) and not within_wait
    ):
        RazziaEntry(member=member, razzia=razzia).save()

    return render(request, templates[razzia_type], locals())


@permission_required("stregreport.host_razzia")
def razzia_menu(request, razzia_type=BreadRazzia.BREAD, new_text=None, title=None):
    razzias = BreadRazzia.objects.filter(razzia_type=razzia_type).order_by('-pk')[:3]
    if len(razzias) == 0:
        return redirect('razzia_new_' + razzia_type)
    return render(request, 'menu.html', locals())


@permission_required("stregreport.host_razzia")
def new_razzia(request, razzia_type=BreadRazzia.BREAD):
    razzia = BreadRazzia(razzia_type=razzia_type)
    razzia.save()

    views = {BreadRazzia.BREAD: 'bread_view', BreadRazzia.FOOBAR: 'foobar_view', BreadRazzia.FNUGFALD: 'fnugfald_view'}

    return redirect(views[razzia_type], razzia_id=razzia.pk)


@permission_required("stregreport.host_razzia")
def razzia_members(request, razzia_id, razzia_type=BreadRazzia.BREAD, title=None):
    razzia = get_object_or_404(BreadRazzia, pk=razzia_id, razzia_type=razzia_type)
    return render(request, 'members.html', locals())


razzia = staff_member_required(razzia)
razzia_view_single = staff_member_required(razzia_view_single)
new_razzia = staff_member_required(new_razzia)
razzia_members = staff_member_required(razzia_members)


@permission_required("stregreport.host_razzia")
def razzia_view(request):
    default_start = timezone.now().today() - datetime.timedelta(days=-180)
    default_end = timezone.now().today()
    start = request.GET.get('start', default_start.isoformat())
    end = request.GET.get('end', default_end.isoformat())
    products = request.GET.get('products', "")
    username = request.GET.get('username', "")
    title = request.GET.get('razzia_title', "Razzia!")

    try:
        product_list = [int(p) for p in products.split(",")]
    except ValueError:
        return render(request, 'error_wizarderror.html', {})

    product_dict = {k.name: 0 for k in Product.objects.filter(id__in=product_list)}
    if len(product_list) != len(product_dict.items()):
        return render(request, 'error_wizarderror.html', {})

    try:
        user = Member.objects.get(username__iexact=username)
    except (Member.DoesNotExist, Member.MultipleObjectsReturned):
        return render(
            request,
            'wizard_view.html',
            {'start': start, 'end': end, 'products': products, 'username': username, 'razzia_title': title},
        )

    start_date = dateparse.parse_date(start)
    end_date = dateparse.parse_date(end)
    sales_to_user = _sales_to_user_in_period(username, start_date, end_date, product_list, product_dict)

    return render(
        request,
        'wizard_view.html',
        {
            'razzia_title': title,
            'username': username,
            'start': start,
            'end': end,
            'products': products,
            'member_name': user.firstname + " " + user.lastname,
            'items_bought': sales_to_user.items(),
        },
    )


razzia_view = staff_member_required(razzia_view)


@permission_required("stregreport.host_razzia")
def razzia_wizard(request):
    if request.method == 'POST':
        return redirect(
            reverse("razzia_view")
            + "?start={0}-{1}-{2}&end={3}-{4}-{5}&products={6}&username=&razzia_title={7}".format(
                int(request.POST['start_year']),
                int(request.POST['start_month']),
                int(request.POST['start_day']),
                int(request.POST['end_year']),
                int(request.POST['end_month']),
                int(request.POST['end_day']),
                request.POST.get('products'),
                request.POST.get('razzia_title'),
            )
        )

    suggested_start_date = timezone.now() - datetime.timedelta(days=-180)
    suggested_end_date = timezone.now()

    start_date_picker = fields.DateField(
        widget=SelectDateWidget(years=[x for x in range(2000, timezone.now().year + 1)])
    )
    end_date_picker = fields.DateField(widget=SelectDateWidget(years=[x for x in range(2000, timezone.now().year + 1)]))

    return render(
        request,
        'wizard.html',
        {
            'start_date_picker': start_date_picker.widget.render("start", suggested_start_date),
            'end_date_picker': end_date_picker.widget.render("end", suggested_end_date),
        },
    )


razzia_wizard = staff_member_required(razzia_wizard)


def _sales_to_user_in_period(username, start_date, end_date, product_list, product_dict):
    result = (
        Product.objects.filter(
            sale__member__username__iexact=username,
            id__in=product_list,
            sale__timestamp__gte=start_date,
            sale__timestamp__lte=end_date,
        )
        .annotate(cnt=Count("id"))
        .values_list("name", "cnt")
    )

    products_bought = {product: count for product, count in result}

    return {product: products_bought.get(product, 0) for product in product_dict}
