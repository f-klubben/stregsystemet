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
from django.db.models import Q
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
        fembers = Member.objects.all()
        imports, duplicates = 0, 0
        import csv
        # get csv reader and ignore header
        reader = csv.reader(csvfile[1:], delimiter=';', quotechar='"')
        for row in reader:
            # logger.info(row)
            # make timestamp compliant to ISO 8601 combined date and time - sigh
            # TODO: smarter handling of '+' or '-', point is moot though, as DK is always either +1 or +2 UTC
            #  also, I don't care as datetime doesn't support '%z' anymore apparently
            split_row = row[3].split('+')
            # remove precision of second-decimal, add back '+' and remove ':' from timezone specification
            # TODO, fix timestamps as Django uses seconds precision - but afair does not account for local timezone
            #  and simply shows UTC
            row[3] = f"{split_row[0][:-8]}"  # +{''.join(split_row[1].split(':'))}"
            mbpay = MobilePayment(member=None, amount=row[2].replace(',', ''),
                                  # timestamp=datetime.datetime.strptime(row[3], "%Y-%m-%dT%H:%M:%S"),
                                  customer_name=row[4], transaction_id=row[7], comment=row[6])

            try:
                # Unique constraint on transaction_id must hold before saving new object
                mbpay.validate_unique()
                # logger.info(f"comment: {mbpay.comment.strip()}")
                # do exact case sensitive match
                match = fembers.filter(username__exact=mbpay.comment.strip())
                if match and match.count() == 0:
                    logger.info(f"found no match for payment with comment: {mbpay.comment}")

                elif match and match.count() == 1:
                    # logger.info(f"matched with username: {match.first().username}")
                    # TODO: also do check on mobilepay name against fember name
                    mbpay.member_guess = match.first()
                    mbpay.member = match.first()
                else:
                    logger.info(f"matched with more than one username: {[x.username for x in match]}")
                mbpay.save()
                imports += 1
            except ValidationError:
                logger.info(f"[paytool] Found duplicate of transmission_id: {mbpay.transaction_id}, ignoring")
                duplicates += 1
        return imports, duplicates

    data = dict()
    if request.method == "POST" and request.FILES:

        csv_file = request.FILES['csv_file']
        csv_file.seek(0)

        data['imports'], data['duplicates'] = parse_csv_and_create_mbpayments(
            str(csv_file.read().decode('utf-8')).splitlines())
        if data['imports'] > 0:
            n = data['imports']
            logger.info(f"have {n} new imports")
            data['mobilepayments'] = MobilePayment.objects.all().order_by('-id')[:n]
        logger.info(data)
    return render(request, "admin/stregsystem/import_mbpay.html", data)


class MemberWidget(s2forms.ModelSelect2Widget):
    model = Member


class MobilePaymentForm(forms.ModelForm):
    class Meta:
        model = MobilePayment
        fields = ('amount', 'member', 'member_guess', 'customer_name', 'comment', 'approval')
        widgets = {"member": MemberWidget,
                   "member_guess": MemberWidget}


@staff_member_required()
def paytool(request):
    paytool_form_set = modelformset_factory(MobilePayment, fields=(
        'amount', 'member', 'member_guess', 'customer_name', 'comment', 'approval'), extra=0,
                                            widgets={"member": MemberWidget,
                                                     "member_guess": MemberWidget()})

    @transaction.atomic
    def submit_mbpayments():
        approved_mbpayments = MobilePayment.objects.filter(
            Q(approval=True) & Q(payment__isnull=True) & (Q(member__isnull=False) | Q(member_guess__isnull=False)))

        for mbpayment in approved_mbpayments:
            # set mobilepayment receiving member to guess if unfilled
            if not mbpayment.member and mbpayment.member_guess:
                mbpayment.member = mbpayment.member_guess

            # todo: write edit-distance matching on non-exact matches?

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
            form.save()
            submit_mbpayments()
            # refresh form after submission
            data['formset'] = get_unprocessed_transactions()

    return render(request, "admin/stregsystem/mobilepaytool.html", data)
