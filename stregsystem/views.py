import datetime
from functools import reduce

from django.db.models import Q
from django.http import HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404, render
from stregsystem.utils import (
    make_active_productlist_query,
    make_room_specific_query
)
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
from .booze import ballmer_peak


def __get_news():
    try:
        return News.objects.filter(stop_date__gte=datetime.datetime.now(), pub_date__lte=datetime.datetime.now()).get()
    except News.DoesNotExist:
        return None


def __get_productlist(room_id):
    l = (
        make_active_productlist_query(Product.objects)
                       .filter(make_room_specific_query(room_id))
    )
    return l

def roomindex(request):
    return HttpResponsePermanentRedirect('/1/')


#    room_list = Room.objects.all().order_by('name', 'description')
#    return render(request, 'stregsystem/roomindex.html', {'room_list': room_list})

def index(request, room_id):
    room = get_object_or_404(Room, pk=int(room_id))
    product_list = __get_productlist(room_id)
    news = __get_news()
    return render(request, 'stregsystem/index.html', locals())

def sale(request, room_id):
    room = get_object_or_404(Room, pk=room_id)
    news = __get_news()
    product_list = __get_productlist(room_id)

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
            'error_msg': ' ' * (len(err.parsed_part) - 4) + 'Fejl her',
            'room': room}
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
    product_list = __get_productlist(room.id)

    # Retrieve products and construct transaction
    products = []
    try:
        for i in bought_ids:
            product = Product.objects.get(Q(pk=i), Q(active=True), Q(deactivate_date__gte=datetime.datetime.now()) | Q(
                deactivate_date__isnull=True), Q(rooms__id=room.id) | Q(rooms=None))
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
    is_ballmer_peaking, bp_minutes, bp_seconds = ballmer_peak(promille)

    cost = order.total

    return render(request, 'stregsystem/index_sale.html', locals())


def usermenu(request, room, member, bought):
    negative_balance = member.balance < 0
    product_list = __get_productlist(room.id)
    news = __get_news()
    promille = member.calculate_alcohol_promille()
    is_ballmer_peaking, bp_minutes, bp_seconds, = ballmer_peak(promille)

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

    _total_by_product = __get_total_by_product(member)
    total_sales = reduce(lambda s, i: s + i[1], _total_by_product, 0)

    negative_balance = member.balance < 0
    stregforbud = member.has_stregforbud()

    return render(request, 'stregsystem/menu_userinfo.html', locals())


def menu_sale(request, room_id, member_id, product_id=None):
    room = Room.objects.get(pk=room_id)
    news = __get_news()
    member = Member.objects.get(pk=member_id, active=True)
    product = None
    try:
        product = Product.objects.get(Q(pk=product_id), Q(active=True), Q(rooms__id=room_id) | Q(rooms=None),
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
