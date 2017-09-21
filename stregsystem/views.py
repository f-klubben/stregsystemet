import datetime
from functools import reduce

from django.db.models import Count, Q, Sum
from django.http import HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404, render
from stregsystem.utils import make_active_productlist_query
from stregsystem.models import (
    Member,
    News,
    Product,
    Room,
    StregForbudError,
    NoMoreInventoryError,
    Order
)
import stregsystem.parser as parser


def __get_news():
    try:
        return News.objects.filter(stop_date__gte=datetime.datetime.now(), pub_date__lte=datetime.datetime.now()).get()
    except News.DoesNotExist:
        return None


def __get_productlist():
    l = (
        Product.objects.filter(make_active_productlist_query())
    )
    return l

def roomindex(request):
    return HttpResponsePermanentRedirect('/1/')


#    room_list = Room.objects.all().order_by('name', 'description')
#    return render(request, 'stregsystem/roomindex.html', {'room_list': room_list})

def index(request, room_id):
    room = get_object_or_404(Room, pk=int(room_id))
    product_list = __get_productlist()
    news = __get_news()
    return render(request, 'stregsystem/index.html', locals())

def sale(request, room_id):
    room = get_object_or_404(Room, pk=room_id)
    news = __get_news()
    product_list = __get_productlist()

    buy_string = request.POST['quickbuy'].strip()
    # Handle empty line
    if buy_string == "":
        return render(request, 'stregsystem/index.html', locals())
    # Extract username and product ids
    try:
        username, bought_ids = parser.parse(buy_string)
    except parser.QuickBuyError as err:
        values = {
            'correct': err.parsed_part,
            'incorrect': err.failed_part,
            'error_ptr': '~' * (len(err.parsed_part)) + '^',
            'error_msg': ' ' * (len(err.parsed_part) - 4) + 'Fejl her'}
        return render(request, 'stregsystem/error_invalidquickbuy.html', values)
    # Fetch member from DB
    try:
        member = Member.objects.get(username=username, active=True)
    except Member.DoesNotExist:
        return render(request, 'stregsystem/error_usernotfound.html', locals())

    if len(bought_ids):
        return quicksale(request, room, member, bought_ids)
    else:
        return usermenu(request, room, member, None)


def quicksale(request, room, member, bought_ids):
    news = __get_news()
    product_list = __get_productlist()

    # Retrieve products and construct transaction
    products = []
    try:
        for i in bought_ids:
            product = Product.objects.get(Q(pk=i), Q(active=True), Q(deactivate_date__gte=datetime.datetime.now()) | Q(
                deactivate_date__isnull=True))
            products.append(product)
    except Product.DoesNotExist:
        return usermenu(request, room, member, None)

    order = Order.from_products(
        member=member,
        products=products,
        room=room
    )

    try:
        order.execute()
    except StregForbudError:
        return render(request, 'stregsystem/error_stregforbud.html', locals())
    except NoMoreInventoryError:
        # @INCOMPLETE this should render with a different template
        return render(request, 'stregsystem/error_stregforbud.html', locals())

    promille = member.calculate_alcohol_promille()

    cost = order.total

    return render(request, 'stregsystem/index_sale.html', locals())


def usermenu(request, room, member, bought):
    negative_balance = member.balance < 0
    product_list = __get_productlist()
    news = __get_news()
    promille = member.calculate_alcohol_promille()
    if member.has_stregforbud():
        return render(request, 'stregsystem/error_stregforbud.html', locals())
    else:
        return render(request, 'stregsystem/menu.html', locals())


def __get_total_by_product(member):
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute("""SELECT name, SUM(sale.price)
                    FROM `stregsystem_sale` as `sale`, `stregsystem_product` as `product`
                    WHERE `member_id` = %s AND product.id = sale.product_id GROUP BY `product_id`""", [member.id])
    l = cursor.fetchall()
    l2 = []
    for a in l:
        l2.append((a[0], int(a[1])))

    return l2


def menu_userinfo(request, room_id, member_id):
    room = Room.objects.get(pk=room_id)
    news = __get_news()
    member = Member.objects.get(pk=member_id, active=True)

    last_sale_list = member.sale_set.order_by('-timestamp')[:10]
    try:
        last_payment = member.payment_set.order_by('-timestamp')[0]
    except IndexError:
        last_payment = None

    total_by_product = __get_total_by_product(member)
    total_sales = reduce(lambda s, i: s + i[1], total_by_product, 0)

    negative_balance = member.balance < 0
    stregforbud = member.has_stregforbud()

    return render(request, 'stregsystem/menu_userinfo.html', locals())


def menu_sale(request, room_id, member_id, product_id=None):
    room = Room.objects.get(pk=room_id)
    news = __get_news()
    member = Member.objects.get(pk=member_id, active=True)
    product = None
    try:
        product = Product.objects.get(Q(pk=product_id), Q(active=True),
                                      Q(deactivate_date__gte=datetime.datetime.now()) | Q(deactivate_date__isnull=True))

        order = Order.from_products(
            member=member,
            room=room,
            products=(product, )
        )

        order.execute()

    except Product.DoesNotExist:
        pass
    except StregForbudError:
        return render(request, 'stregsystem/error_stregforbud.html', locals())
    except NoMoreInventoryError:
        # @INCOMPLETE this should render with a different template
        return render(request, 'stregsystem/error_stregforbud.html', locals())
    # Refresh member, to get new amount
    member = Member.objects.get(pk=member_id, active=True)
    return usermenu(request, room, member, product)


def ranks(request, year=None):
    if (year):
        return ranks_for_year(request, int(year))
    else:
        return ranks_for_year(request, next_fjule_party_year())


# renders stats for the year starting at first friday in december (year - 1) to the first friday in december (year)
# both at 10 o'clock
def ranks_for_year(request, year):
    if (year <= 1900 or year > 9999):
        return render(request, 'stregsystem/error_ranksnotfound.html', locals())
    milk = [2, 3, 4, 5, 6, 7, 8, 9, 10, 16, 17, 18, 19, 20, 24, 25, 43, 44, 45]
    caffeine = [11, 12, 30, 32, 34, 35, 36, 37, 39, 1787, 1790, 1791, 1795, 1799, 1800, 1803]
    beer = [13, 14, 29, 42, 47, 54, 65, 66, 1773, 1776, 1777, 1779, 1780, 1783, 1793, 1794]

    FORMAT = '%d/%m/%Y kl. %H:%M'
    from_time = fjule_party(year - 1)
    to_time = fjule_party(year)
    kr_stat_list = sale_money_rank(from_time, to_time)
    beer_stat_list = sale_product_rank(beer, from_time, to_time)
    caffeine_stat_list = sale_product_rank(caffeine, from_time, to_time)
    milk_stat_list = sale_product_rank(milk, from_time, to_time)
    if not len(kr_stat_list) and not len(beer_stat_list) and not len(caffeine_stat_list) and not len(milk_stat_list):
        return render(request, 'stregsystem/error_ranksnotfound.html', locals())
    from_time_string = from_time.strftime(FORMAT)
    to_time_string = to_time.strftime(FORMAT)
    current_date = datetime.datetime.now()
    is_ongoing = current_date > from_time and current_date <= to_time
    return render(request, 'stregsystem/ranks.html', locals())


# gives a list of tuples (int_rank, string_username, int_value) of rankings of money spent between from_time and to_time.
# Limit is the maximum size of the returned list.
def sale_money_rank(from_time, to_time, rank_limit=10):
    try:
        stat_list = list(map(lambda x, y: (y, x.username, money(x.sale__price__sum)),
                             Member.objects.filter(active=True, sale__timestamp__gt=from_time,
                                                   sale__timestamp__lte=to_time).annotate(Sum('sale__price')).order_by(
                                 '-sale__price__sum', 'username')[:rank_limit], range(1, rank_limit + 1)))
    except:
        stat_list = {}
    return stat_list


# gives a list of tuples (int_rank, string_username, int_value) of rankings of sales of the specified products done between from_time and to_time.
# Limit is the maximum size of the returned list.
def sale_product_rank(ids, from_time, to_time, rank_limit=10):
    try:
        query = reduce(lambda x, y: x | y, [Q(sale__product__id=z) for z in ids])
        # query &= Q(active=True)
        query &= Q(sale__timestamp__gt=from_time)
        query &= Q(sale__timestamp__lte=to_time)
        stat_list = list(map(lambda x, y: (y, x.username, x.sale__count),
                             Member.objects.filter(query).annotate(Count('sale')).order_by('-sale__count', 'username')[
                             :rank_limit], range(1, rank_limit + 1)))
    except:
        stat_list = {}
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
