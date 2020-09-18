import datetime
import logging

from django.core.exceptions import ValidationError
from django.core.files.uploadhandler import MemoryFileUploadHandler
from django.db import transaction
from django.forms import modelformset_factory

import stregsystem.parser as parser
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.conf import settings
from django.db.models import Q, Model
from django import forms
from django.http import HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
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
    StregForbudError, MobilePayment
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
    return (
        make_active_productlist_query(Product.objects).filter(make_room_specific_query(room_id))
    )


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
        sale_hints = ["<span class=\"username\">{}</span>".format(member.username)]
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
        return render(request, 'stregsystem/error_stregforbud.html', locals(), status=402)
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


def menu_userpay(request, room_id, member_id):
    room = Room.objects.get(pk=room_id)
    member = Member.objects.get(pk=member_id, active=True)

    amounts = {100, 200}

    try:
        last_payment = member.payment_set.order_by('-timestamp')[0]
        amounts.add(last_payment.amount / 100.0)
    except IndexError:
        last_payment = None

    negative_balance = member.balance < 0
    if negative_balance:
        amounts.add(- member.balance / 100.0)

    amounts = sorted(amounts)

    return render(request, 'stregsystem/menu_userpay.html', locals())


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
            products=(product,)
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
@permission_required("stregsystem.import_batch_payments")
def batch_payment(request):
    PaymentFormSet = forms.modelformset_factory(
        Payment,
        fields=("member", "amount"),
        widgets={"member": forms.Select(attrs={"class": "select2"})}
    )
    if request.method == "POST":
        formset = PaymentFormSet(request.POST, request.FILES)
        if formset.is_valid():
            # @HACK For some reason django formsets get different member
            # instances with the same values instead of the same instance. This
            # means that if we update the member balance and save it, then
            # repeat, the second write will overwrite the first. In case you
            # don't know, that's not good.
            # To work around this we have to set all the member instances to be
            # the same if they have the same id. This is very, although
            # slightly less, bad - Jesper Jensen 16/02-2017
            payments = formset.save(commit=False)

            # @HACK: We need to consolidate all the member so they are the same
            # instances. We do this by just saving the first one and setting
            # all the remaining with the same id to be that instance aswell.
            members = {}
            for payment in payments:
                if payment.member.id not in members:
                    members[payment.member.id] = payment.member
                payment.member = members[payment.member.id]

            for payment in payments:
                payment.save()

            return render(
                request,
                "admin/stregsystem/batch_payment_done.html",
                {}
            )
    else:
        formset = PaymentFormSet(queryset=Payment.objects.none())
    return render(request, "admin/stregsystem/batch_payment.html", {
        "formset": formset,
        "select2_js": settings.SELECT2_JS,
        "select2_css": settings.SELECT2_CSS,
    })


logger = logging.getLogger('django')


@staff_member_required()
def import_mobilepay_csv(request):
    def parse_csv_and_create_mbpayments(csvfile):
        imported_transactions, duplicate_transactions = 0, 0
        import csv
        # get csv reader and ignore header
        reader = csv.reader(csvfile[1:], delimiter=';', quotechar='"')
        for row in reader:
            # make timestamp compliant to ISO 8601 combined date and time, because MobilePay thinks they're cool adding
            #  7 decimals of precision to timestamps, however ISO 8601 only allows for 3-6 decimals of precision
            # TODO: make check for 7 digits of precision before converting in case MobilePay fixes this in future
            split_row = row[3].split('+')
            row[3] = f"{split_row[0][:-1]}+{split_row[1]}"

            mobile_payment = MobilePayment(member=None, amount=row[2].replace(',', ''),
                                           timestamp=datetime.datetime.fromisoformat(row[3]), customer_name=row[4],
                                           transaction_id=row[7], comment=row[6], payment=None)
            try:
                # unique constraint on transaction_id and payment-foreign key must hold before saving new object
                mobile_payment.validate_unique()

                # do exact case sensitive match
                match = Member.objects.filter(username__exact=mobile_payment.comment.strip())
                if match.count() == 0:
                    # no match, maybe do edit-distance checking for nearest match and remove common fluff such as emoji
                    #  could/should be combined with a match against MobilePay-provided customer name
                    pass
                elif match.count() == 1:
                    # TODO: also do check on mobilepay name against fember name?
                    mobile_payment.member_guess = match.first()
                    mobile_payment.member = match.first()
                elif match.count() > 1:
                    # something is very wrong, there should be no active users which are duplicates post PR #178
                    #  TODO: how to properly raise error in stregsystem? simply log-entry?
                    pass
                # TODO: do LogEntry
                mobile_payment.save()
                imported_transactions += 1
            except ValidationError:
                duplicate_transactions += 1
        return imported_transactions, duplicate_transactions

    data = dict()
    if request.method == "POST" and request.FILES:
        # Prepare uploaded CSV to be read
        csv_file = request.FILES['csv_file']
        csv_file.seek(0)

        data['imports'], data['duplicates'] = parse_csv_and_create_mbpayments(
            str(csv_file.read().decode('utf-8')).splitlines())
        if data['imports'] > 0:
            data['mobilepayments'] = MobilePayment.objects.all().order_by('-id')[:data['imports']]
    return render(request, "admin/stregsystem/import_mbpay.html", data)


class MemberWidget(s2forms.ModelSelect2Widget):
    search_fields = ['username__icontains', 'firstname__icontains', 'lastname__icontains', 'email__icontains']
    model = Member


@staff_member_required()
def paytool(request):
    paytool_form_set = modelformset_factory(MobilePayment, extra=0, widgets={"member": MemberWidget}, fields=(
        'amount', 'member', 'member_guess', 'customer_name', 'comment', 'approval'))

    @transaction.atomic
    def submit_mbpayments():
        approved_mbpayments = MobilePayment.objects.filter(
            Q(approval=True) & Q(payment__isnull=True) & (Q(member__isnull=False) | Q(member_guess__isnull=False)))

        for mbpayment in approved_mbpayments:
            # set mobilepayment receiving member to guess if unfilled
            if not mbpayment.member and mbpayment.member_guess:
                mbpayment.member = mbpayment.member_guess

            # create payment for transaction, assign payment to mobilepayment and save both
            # note that key to payment is not available when chaining a save call, hence this structure
            payment = Payment(member=mbpayment.member, amount=mbpayment.amount)
            payment.save()
            mbpayment.payment = payment
            mbpayment.save()

    def get_unprocessed_transactions():
        return paytool_form_set(queryset=MobilePayment.objects.filter(Q(approval=False) | Q(payment__isnull=True)))

    data = {
        'mbpayment': MobilePayment.objects.all(),
    }

    if request.method == "GET":
        data['formset'] = get_unprocessed_transactions()

    elif request.method == "POST":
        form = paytool_form_set(request.POST)

        # todo: enable form-errors to be shown to user, since we are using a custom template for form, maybe difficult?
        if form.is_valid():
            form.save()  # commit=false here? it was done for batch because of reference thing
            submit_mbpayments()
            # refresh form after submission
            data['formset'] = get_unprocessed_transactions()

    return render(request, "admin/stregsystem/mobilepaytool.html", data)
