import datetime
from functools import reduce

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDay
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from stregsystem.models import Member, Product, Sale


def reports(request):
    return render(request, 'admin/stregsystem/report/index.html', locals())


reports = staff_member_required(reports)


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


def bread(request):
    if request.method == 'POST':
        return bread_view(request, request.POST['username'])
    else:
        return bread_view(request, None)


bread = staff_member_required(bread)


def bread_view(request, queryname):
    if queryname is not None:
        result = list(Member.objects.filter(username__iexact=queryname))
        if len(result) > 0:
            member = result[0]

    return render(request, 'admin/stregsystem/razzia/bread.html', locals())


def ranks(request, year=None):
    if year:
        return ranks_for_year(request, int(year))
    else:
        return ranks_for_year(request, next_fjule_party_year())


ranks = staff_member_required(ranks)


def sales_product(request, ids, from_time, to_time, error=None):
    date_format = '%Y-%m-%d'

    if error is not None:
        return render(request, 'admin/stregsystem/report/error_invalidsalefetch.html', {'error': error})

    try:
        try:
            from_date_time = datetime.datetime.strptime(from_time, date_format)
        except:
            from_date_time = first_of_month(datetime.datetime.now())
        from_time = from_date_time.strftime(date_format)

        try:
            to_date_time = late(datetime.datetime.strptime(to_time, date_format))
        except:
            to_date_time = datetime.datetime.now()
        to_time = to_date_time.strftime(date_format)
        sales = []
        if ids and len(ids) > 0:
            products = reduce(lambda a, b: a + str(b) + ' ', ids, '')
            query = reduce(lambda x, y: x | y, [Q(id=z) for z in ids])
            query &= Q(sale__timestamp__gt=from_date_time)
            query &= Q(sale__timestamp__lte=to_date_time)
            result = Product.objects.filter(query).annotate(Count('sale'), Sum('sale__price'))

            count = 0
            sum = 0
            for r in result:
                sales.append((r.pk, r.name, r.sale__count, money(r.sale__price__sum)))
                count = count + r.sale__count
                sum = sum + r.sale__price__sum

            sales.append(('', 'TOTAL', count, money(sum)))
    except Exception as e:
        return render(request, 'admin/stregsystem/report/error_invalidsalefetch.html', {'error': e.__str__()})
    return render(request, 'admin/stregsystem/report/sales.html', locals())


# renders stats for the year starting at first friday in december (year - 1) to the first friday in december (year)
# both at 10 o'clock
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
    current_date = datetime.datetime.now()
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
    current_date = datetime.datetime.now()
    fjule_party_this_year = fjule_party(current_date.year)
    if current_date > fjule_party_this_year:
        return current_date.year
    return current_date.year - 1


# year of the next fjuleparty
def next_fjule_party_year():
    current_date = datetime.datetime.now()
    fjule_party_this_year = fjule_party(current_date.year)
    if current_date <= fjule_party_this_year:
        return current_date.year
    return current_date.year + 1


# date of fjuleparty (first friday of december) for the given year at 10 o'clock
def fjule_party(year):
    first_december = datetime.datetime(year, 12, 1, 22)
    days_to_add = (11 - first_december.weekday()) % 7
    return first_december + datetime.timedelta(days=days_to_add)


def money(value):
    if value is None:
        value = 0
    return "{0:.2f}".format(value / 100.0)


def parse_id_string(id_string):
    try:
        return list(map(int, id_string.split(' ')))
    except ValueError as ex:
        raise RuntimeError("The list contained an invalid id: {}".format(ex.__str__()))


def late(date):
    return datetime.datetime(date.year, date.month, date.day, 23, 59, 59)


def first_of_month(date):
    return datetime.datetime(date.year, date.month, 1, 23, 59, 59)


def daily(request):
    current_date = datetime.datetime.now().replace(hour=0, minute=0, second=0)
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

    return render(request, 'admin/stregsystem/report/daily.html', locals())


def sales_api(request):
    startTime_month = timezone.now() - datetime.timedelta(days=30)
    qs = (Sale.objects
          .filter(timestamp__gt=startTime_month)
          .order_by("timestamp")
          .annotate(day=TruncDay('timestamp'))
          .values('day')
          .annotate(c=Count('id'))
          .order_by())
    db_sales = {i["day"].date(): i["c"] for i in qs}
    base = timezone.now().date()
    date_list = [base - datetime.timedelta(days=x) for x in range(0, 30)]

    sales = []
    for date in date_list:
        if date in db_sales:
            sales.append(db_sales[date])
        else:
            sales.append(0)

    items = {
        "day": date_list,
        "sales": sales,
    }
    return JsonResponse(items)


daily = staff_member_required(daily)
