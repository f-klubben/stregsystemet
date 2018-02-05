import datetime

import stregsystem.parser as parser
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django import forms
from django.http import HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
import stregsystem.parser as parser
from django_select2 import forms as s2forms


from stregsystem import parser
from stregsystem.models import (
    Member,
    Payment,
    News,
    NoMoreInventoryError,
    Order,
    Product,
    Room,
    Sale,
    StregForbudError
)
from stregsystem.utils import (
    make_active_productlist_query,
    make_room_specific_query
)

from .booze import ballmer_peak


def __get_news():
    try:
        return News.objects.filter(stop_date__gte=timezone.now(), pub_date__lte=timezone.now()).get()
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


def _multibuy_hint(now, member):
    # Get a timestamp to fetch sales for the member for the last 60 sec
    earliest_recent_purchase = now - datetime.timedelta(seconds=60)
    # get the sales with this timestamp
    recent_purchases = (
        Sale.objects
            .filter(member=member, timestamp__gt=earliest_recent_purchase)
    )
    number_of_recent_distinct_purchases = recent_purchases.values('timestamp').distinct().count()

    # add hint for multibuy
    if number_of_recent_distinct_purchases > 1:
        sale_dict = {}
        for sale in recent_purchases:
            if not str(sale.product.id) in sale_dict:
                sale_dict[str(sale.product.id)] = 1
            else:
                sale_dict[str(sale.product.id)] = sale_dict[str(sale.product.id)] + 1
        sale_hints = [member.username]
        for key in sale_dict:
            if sale_dict[key] > 1:
                sale_hints.append("{}:{}".format(key, sale_dict[key]))
            else:
                sale_hints.append(key)
        return (True, ' '.join(sale_hints))

    return (False, None)


def quicksale(request, room, member, bought_ids):
    news = __get_news()
    product_list = __get_productlist(room.id)
    now = timezone.now()

    # Retrieve products and construct transaction
    products = []
    try:
        for i in bought_ids:
            product = Product.objects.get(Q(pk=i), Q(active=True), Q(deactivate_date__gte=now) | Q(
                deactivate_date__isnull=True), Q(rooms__id=room.id) | Q(rooms=None))
            products.append(product)
    except Product.DoesNotExist:
        return render(request, 'stregsystem/error_productdoesntexist.html', {'failedProduct': i, 'room': room})

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

    give_multibuy_hint, sale_hints = _multibuy_hint(now, member)

    return render(request, 'stregsystem/index_sale.html', locals())


def usermenu(request, room, member, bought, from_sale=False):
    negative_balance = member.balance < 0
    product_list = __get_productlist(room.id)
    news = __get_news()
    promille = member.calculate_alcohol_promille()
    is_ballmer_peaking, bp_minutes, bp_seconds, = ballmer_peak(promille)

    give_multibuy_hint, sale_hints = _multibuy_hint(timezone.now(), member)
    give_multibuy_hint = give_multibuy_hint and from_sale

    if member.has_stregforbud():
        return render(request, 'stregsystem/error_stregforbud.html', locals())
    else:
        return render(request, 'stregsystem/menu.html', locals())


def menu_userinfo(request, room_id, member_id):
    room = Room.objects.get(pk=room_id)
    news = __get_news()
    member = Member.objects.get(pk=member_id, active=True)

    last_sale_list = member.sale_set.order_by('-timestamp')[:10]
    try:
        last_payment = member.payment_set.order_by('-timestamp')[0]
    except IndexError:
        last_payment = None

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
                                      Q(deactivate_date__gte=timezone.now()) | Q(deactivate_date__isnull=True))

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
    return usermenu(request, room, member, product, from_sale=True)


@staff_member_required()
def batch_payment(request):
    PaymentFormSet = forms.modelformset_factory(
        Payment,
        fields=("member", "amount"),
        can_delete=True,
        widgets={"member": s2forms.Select2Widget}
    )
    if request.method == "POST":
        formset = PaymentFormSet(request.POST, request.FILES)
        if formset.is_valid():
            formset.save()
            return render(
                request,
                "admin/stregsystem/batch_payment_done.html",
                {}
            )
    else:
        formset = PaymentFormSet(queryset=Payment.objects.none())
    return render(request, "admin/stregsystem/batch_payment.html", {
        "formset": formset,
    })
