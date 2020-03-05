import datetime
from functools import reduce

import pytz
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
from stregreport.forms import CategoryReportForm
from stregsystem.models import Category, Member, Product, Sale
from stregreport.models import BreadRazzia, RazziaEntry
from stregsystem.templatetags.stregsystem_extras import money

@permission_required("stregsystem.access_sales_reports")
def reports(request):
    return render(request, 'admin/stregsystem/report/index.html', locals())


reports = staff_member_required(reports)


@permission_required("stregsystem.access_sales_reports")
def sales(request):
    if request.method == 'POST':
        try:
            return sales_product(request,
                                 parse_id_string(request.POST['products']),
                                 request.POST['from_date'],
                                 request.POST['to_date'])
        except RuntimeError as ex:
            return sales_product(request, None, None, None, error=ex.__str__())
    else:
        return sales_product(request, None, None, None)


sales = staff_member_required(sales)


@permission_required("stregreport.host_razzia")
def razzia(request, razzia_id, razzia_type=BreadRazzia.BREAD, title=None):
    if request.method == 'POST':
        return razzia_view_single(request, razzia_id, request.POST['username'], razzia_type=razzia_type, title=title)
    else:
        return razzia_view_single(request, razzia_id, None, razzia_type=razzia_type, title=title)


@permission_required("stregreport.host_razzia")
def razzia_view_single(request, razzia_id, queryname, razzia_type=BreadRazzia.BREAD, title=None):
    razzia = get_object_or_404(BreadRazzia, pk=razzia_id, razzia_type=razzia_type)
    if queryname is not None:
        result = list(Member.objects.filter(username__iexact=queryname))
        if len(result) > 0:
            member = result[0]
            entries = list(razzia.razziaentry_set.filter(member__pk=member.pk).order_by('-time'))
            already_used = len(entries) > 0
            if already_used:
                entry = entries[0]
            if not already_used or razzia_type == BreadRazzia.FOOBAR:
                RazziaEntry(member = member, razzia = razzia).save()

    templates = {
        BreadRazzia.BREAD: 'admin/stregsystem/razzia/bread.html',
        BreadRazzia.FOOBAR: 'admin/stregsystem/razzia/foobar.html'
    }
    return render(request, templates[razzia_type], locals())


@permission_required("stregreport.host_razzia")
def razzia_menu(request, razzia_type=BreadRazzia.BREAD, new_text=None, title=None):
    razzias = BreadRazzia.objects.filter(razzia_type=razzia_type).order_by('-pk')[:3]
    if len(razzias) == 0:
        return redirect('razzia_new_' + razzia_type)
    return render(request, 'admin/stregsystem/razzia/menu.html', locals())


@permission_required("stregreport.host_razzia")
def new_razzia(request, razzia_type=BreadRazzia.BREAD):
    razzia = BreadRazzia(razzia_type=razzia_type)
    razzia.save()

    views = {
        BreadRazzia.BREAD: 'bread_view',
        BreadRazzia.FOOBAR: 'foobar_view'
    }

    return redirect(views[razzia_type], razzia_id=razzia.pk)


@permission_required("stregreport.host_razzia")
def razzia_members(request, razzia_id, razzia_type=BreadRazzia.BREAD, title=None):
    razzia = get_object_or_404(BreadRazzia, pk=razzia_id, razzia_type=razzia_type)
    return render(request, 'admin/stregsystem/razzia/members.html', locals())


razzia = staff_member_required(razzia)
razzia_view_single = staff_member_required(razzia_view_single)
new_razzia = staff_member_required(new_razzia)
razzia_members = staff_member_required(razzia_members)


def _sales_to_user_in_period(username, start_date, end_date, product_list, product_dict):
    result = (
        Product.objects
            .filter(
            sale__member__username__iexact=username,
            id__in=product_list,
            sale__timestamp__gte=start_date,
            sale__timestamp__lte=end_date)
            .annotate(cnt=Count("id"))
            .values_list("name", "cnt")
    )

    products_bought = {product: count for product, count in result}

    return {product: products_bought.get(product, 0) for product in product_dict}


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
        return render(request, 'admin/stregsystem/razzia/error_wizarderror.html', {})

    product_dict = {k.name: 0 for k in Product.objects.filter(id__in=product_list)}
    if len(product_list) != len(product_dict.items()):
        return render(request, 'admin/stregsystem/razzia/error_wizarderror.html', {})

    try:
        user = Member.objects.get(username__iexact=username)
    except (Member.DoesNotExist, Member.MultipleObjectsReturned):
        return render(request, 'admin/stregsystem/razzia/wizard_view.html',
                      {
                          'start': start,
                          'end': end,
                          'products': products,
                          'username': username,
                          'razzia_title': title}
                      )

    start_date = dateparse.parse_date(start)
    end_date = dateparse.parse_date(end)
    sales_to_user = _sales_to_user_in_period(username, start_date, end_date, product_list, product_dict)

    return render(request, 'admin/stregsystem/razzia/wizard_view.html',
                  {
                      'razzia_title': title,
                      'username': username,
                      'start': start,
                      'end': end,
                      'products': products,
                      'member_name': user.firstname + " " + user.lastname,
                      'items_bought': sales_to_user.items(),
                  })


razzia_view = staff_member_required(razzia_view)


@permission_required("stregreport.host_razzia")
def razzia_wizard(request):
    if request.method == 'POST':
        return redirect(
            reverse("razzia_view") + "?start={0}-{1}-{2}&end={3}-{4}-{5}&products={6}&username=&razzia_title={7}"
            .format(int(request.POST['start_year']),
                    int(request.POST['start_month']),
                    int(request.POST['start_day']),
                    int(request.POST['end_year']), int(request.POST['end_month']),
                    int(request.POST['end_day']),
                    request.POST.get('products'),
                    request.POST.get('razzia_title')))

    suggested_start_date = timezone.now() - datetime.timedelta(days=-180)
    suggested_end_date = timezone.now()

    start_date_picker = fields.DateField(
        widget=SelectDateWidget(years=[x for x in range(2000, timezone.now().year + 1)]))
    end_date_picker = fields.DateField(
        widget=SelectDateWidget(years=[x for x in range(2000, timezone.now().year + 1)]))

    return render(request, 'admin/stregsystem/razzia/wizard.html',
                  {
                      'start_date_picker': start_date_picker.widget.render("start", suggested_start_date),
                      'end_date_picker': end_date_picker.widget.render("end", suggested_end_date)},
                  )


razzia_wizard = staff_member_required(razzia_wizard)


def ranks(request, year=None):
    if year:
        return ranks_for_year(request, int(year))
    else:
        return ranks_for_year(request, next_fjule_party_year())


ranks = staff_member_required(ranks)


@permission_required("stregsystem.access_sales_reports")
def sales_product(request, ids, from_time, to_time, error=None):
    date_format = '%Y-%m-%d'

    if error is not None:
        return render(request, 'admin/stregsystem/report/error_invalidsalefetch.html', {'error': error})

    try:
        from_time_date = datetime.datetime.strptime(from_time, date_format)
        from_date_time_tz_aware = timezone.datetime(
            from_time_date.year,
            from_time_date.month,
            from_time_date.day,
            tzinfo=pytz.UTC
        )
    except (ValueError, TypeError):
        from_date_time_tz_aware = first_of_month(timezone.now())
    from_time = from_date_time_tz_aware.strftime(date_format)

    try:
        to_date_time = late(timezone.datetime.strptime(to_time, date_format))
        to_date_time_tz_aware = timezone.datetime(
            to_date_time.year,
            to_date_time.month,
            to_date_time.day,
            tzinfo=pytz.UTC
        )
    except (ValueError, TypeError):
        to_date_time = timezone.now()
    to_time = to_date_time.strftime(date_format)
    sales = []
    if ids is not None and len(ids) > 0:
        products = reduce(lambda a, b: a + str(b) + ' ', ids, '')
        query = reduce(lambda x, y: x | y, [Q(id=z) for z in ids])
        query &= Q(sale__timestamp__gt=from_date_time_tz_aware)
        query &= Q(sale__timestamp__lte=to_date_time_tz_aware)
        result = Product.objects.filter(query).annotate(Count('sale'), Sum('sale__price'))

        count = 0
        sum = 0
        for r in result:
            sales.append((r.pk, r.name, r.sale__count, money(r.sale__price__sum)))
            count = count + r.sale__count
            sum = sum + r.sale__price__sum

        sales.append(('', 'TOTAL', count, money(sum)))

    return render(request, 'admin/stregsystem/report/sales.html', locals())


# renders stats for the year starting at first friday in december (year - 1) to the first friday in december (year)
# both at 10 o'clock
@permission_required("stregsystem.access_sales_reports")
def ranks_for_year(request, year):
    if (year <= 1900 or year > 9999):
        return render(request, 'admin/stregsystem/report/error_ranksnotfound.html', locals())
    milk = [2, 3, 4, 5, 6, 7, 8, 9, 10, 16, 17, 18, 19, 20, 24, 25, 43, 44, 45, 1865]
    caffeine = [11, 12, 30, 34, 37, 1787, 1790, 1791, 1795, 1799, 1800, 1803, 1804, 1837, 1864]
    beer = [13, 14, 29, 42, 47, 54, 65, 66, 1773, 1776, 1777, 1779, 1780, 1783, 1793, 1794, 1807, 1808, 1809, 1820,
            1822, 1840, 1844, 1846, 1847, 1853, 1855, 1856, 1858, 1859]
    coffee = [32, 35, 36, 39]
    vitamin = [1850, 1851, 1852, 1863]

    FORMAT = '%d/%m/%Y kl. %H:%M'
    last_year = year - 1
    from_time = fjule_party(year - 1)
    to_time = fjule_party(year)
    kr_stat_list = sale_money_rank(from_time, to_time)
    beer_stat_list = sale_product_rank(beer, from_time, to_time)
    caffeine_stat_list = sale_product_rank(caffeine, from_time, to_time)
    milk_stat_list = sale_product_rank(milk, from_time, to_time)
    coffee_stat_list = sale_product_rank(coffee, from_time, to_time)
    vitamin_stat_list = sale_product_rank(vitamin, from_time, to_time)
    from_time_string = from_time.strftime(FORMAT)
    to_time_string = to_time.strftime(FORMAT)
    current_date = timezone.now()
    is_ongoing = current_date > from_time and current_date <= to_time
    return render(request, 'admin/stregsystem/report/ranks.html', locals())


# gives a list of member objects, with the additional field sale__count, with the number of sales which are in the parameter id
def sale_product_rank(ids, from_time, to_time, rank_limit=10):
    stat_list = Member.objects.filter(sale__timestamp__gt=from_time, sale__timestamp__lte=to_time,
                                      sale__product__in=ids).annotate(Count('sale')).order_by('-sale__count',
                                                                                              'username')[:rank_limit]
    return stat_list


# gives a list of member object, with the additional field sale__price__sum__formatted which is the number of money spent in the period given.
def sale_money_rank(from_time, to_time, rank_limit=10):
    stat_list = Member.objects.filter(active=True, sale__timestamp__gt=from_time,
                                      sale__timestamp__lte=to_time).annotate(Sum('sale__price')).order_by(
        '-sale__price__sum', 'username')[:rank_limit]
    for member in stat_list:
        member.sale__price__sum__formatted = money(member.sale__price__sum)
    return stat_list


# year of the last fjuleparty
def last_fjule_party_year():
    current_date = timezone.now()
    fjule_party_this_year = fjule_party(current_date.year)
    if current_date > fjule_party_this_year:
        return current_date.year
    return current_date.year - 1


# year of the next fjuleparty
def next_fjule_party_year():
    current_date = timezone.now()
    fjule_party_this_year = fjule_party(current_date.year)
    if current_date <= fjule_party_this_year:
        return current_date.year
    return current_date.year + 1


# date of fjuleparty (first friday of december) for the given year at
# 10 o'clock
def fjule_party(year):
    first_december = timezone.datetime(
        year,
        12,
        1,
        22,
        tzinfo=pytz.timezone("Europe/Copenhagen")
    )
    days_to_add = (11 - first_december.weekday()) % 7
    return first_december + datetime.timedelta(days=days_to_add)


def parse_id_string(id_string):
    try:
        return list(map(int, id_string.split(' ')))
    except ValueError as ex:
        raise RuntimeError("The list contained an invalid id: {}".format(ex.__str__()))


def late(date):
    return timezone.datetime(date.year, date.month, date.day, 23, 59, 59)


def first_of_month(date):
    return timezone.datetime(date.year, date.month, 1, 23, 59, 59)


@permission_required("stregsystem.access_sales_reports")
def daily(request):
    current_date = timezone.now().replace(hour=0, minute=0, second=0)
    latest_sales = (Sale.objects
                    .prefetch_related('product', 'member')
                    .order_by('-timestamp')[:7])
    top_today = (Product.objects
                 .filter(sale__timestamp__gt=current_date)
                 .annotate(Count('sale'))
                 .order_by('-sale__count')[:7])

    startTime_day = timezone.now() - datetime.timedelta(hours=24)
    revenue_day = (Sale.objects
                   .filter(timestamp__gt=startTime_day)
                   .aggregate(Sum("price"))
                   ["price__sum"]) or 0.0
    startTime_month = timezone.now() - datetime.timedelta(days=30)
    revenue_month = (Sale.objects
                     .filter(timestamp__gt=startTime_month)
                     .aggregate(Sum("price"))
                     ["price__sum"]) or 0.0
    top_month_category = (Category.objects
                          .filter(product__sale__timestamp__gt=startTime_month)
                          .annotate(sale=Count("product__sale"))
                          .order_by("-sale")[:7])

    return render(request, 'admin/stregsystem/report/daily.html', locals())


def sales_api(request):
    startTime_month = timezone.now() - datetime.timedelta(days=30)
    qs = (Sale.objects
          .filter(timestamp__gt=startTime_month)
          .annotate(day=TruncDay('timestamp'))
          .values('day')
          .annotate(c=Count('*'))
          .annotate(r=Sum('price'))
          )
    db_sales = {i["day"].date(): (i["c"], money(i["r"])) for i in qs}
    base = timezone.now().date()
    date_list = [base - datetime.timedelta(days=x) for x in range(0, 30)]

    sales_list = []
    revenue_list = []
    for date in date_list:
        if date in db_sales:
            sales, revenue = db_sales[date]
            sales_list.append(sales)
            revenue_list.append(revenue)
        else:
            sales_list.append(0)
            revenue_list.append(0)

    items = {
        "day": date_list,
        "sales": sales_list,
        "revenue": revenue_list,
    }
    return JsonResponse(items)


daily = staff_member_required(daily)


@permission_required("stregsystem.access_sales_reports")
def user_purchases_in_categories(request):
    form = CategoryReportForm()
    data = None
    header = None
    if request.method == 'POST':
        form = CategoryReportForm(request.POST)
        if form.is_valid():
            categories = form.cleaned_data['categories']

            # @SPEED: This is not a good solution for maximum speed,
            # however neither is using MySQL. Django doesn't want to
            # group by category_id correctly.
            # -- Troels 2017-10-04

            user_sales_per_category = {}
            for c in categories:
                user_sales_per_category_q = (
                    Member.objects
                    .filter(sale__product__categories=c)
                    .annotate(sales=Count("*"))
                    .order_by("sale__product__categories")
                    .values_list(
                        "id",
                        "sales",
                        "sale__product__categories__name",
                    )
                )

                for user_id, sale_count, category_name in user_sales_per_category_q:
                    if user_id not in user_sales_per_category:
                        user_sales_per_category[user_id] = {}
                    user_sales_per_category[user_id][category_name] = sale_count

            users = (
                Member.objects
                .filter(sale__product__categories__in=categories)
                .annotate(total_sales=Count("*"))
                .order_by("-total_sales")
                .values_list(
                    "id",
                    "username",
                    "total_sales",
                )
            )

            header = categories.values_list("name", flat=True)
            data = []
            for user_id, username, total_sales in users:
                category_assoc = []
                for h in header:
                    this_sales = user_sales_per_category[user_id]
                    if h in this_sales:
                        category_assoc.append(this_sales[h])
                    else:
                        category_assoc.append(0)
                data.append((username, total_sales, category_assoc))

    return render(
        request,
        'admin/stregsystem/report/user_purchases_in_categories.html',
        {
            "form": form,
            "data": data,
            "header": header,
        }
    )
