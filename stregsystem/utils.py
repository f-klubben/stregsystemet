import datetime
import logging
import re
import csv

from django.utils.dateparse import parse_datetime
from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.test.runner import DiscoverRunner

from django.db.models import Count, F, Q, QuerySet
from django.utils import timezone

import qrcode
import qrcode.image.svg

import urllib.parse

from stregsystem.models import Category, Member, Sale, Product

logger = logging.getLogger(__name__)


def make_active_productlist_query(queryset) -> QuerySet:
    now = timezone.now()
    # Create a query for the set of products that MIGHT be active. Might
    # because they can be out of stock. Which we compute later
    active_candidates = queryset.filter(
        Q(active=True)
        & (Q(deactivate_date=None) | Q(deactivate_date__gte=now))
        & (Q(start_date__isnull=True) | Q(start_date__lte=now.date()))
    )
    # This query selects all the candidates that are out of stock.
    candidates_out_of_stock = (
        active_candidates.filter(sale__timestamp__gt=F("start_date"))
        .annotate(c=Count("sale__id"))
        .filter(c__gte=F("quantity"))
        .values("id")
    )
    # We can now create a query that selects all the candidates which are not
    # out of stock.
    return active_candidates.exclude(Q(start_date__isnull=False) & Q(id__in=candidates_out_of_stock))


def make_inactive_productlist_query(queryset) -> QuerySet:
    now = timezone.now()
    # Create a query of things which are definitively inactive. Some of the ones
    # filtered here might be out of stock, but we include that later.
    inactive_candidates = queryset.exclude(
        Q(active=True) & (Q(deactivate_date=None) | Q(deactivate_date__gte=now))
    ).values("id")
    inactive_out_of_stock = (
        queryset.filter(sale__timestamp__gt=F("start_date"))
        .annotate(c=Count("sale__id"))
        .filter(c__gte=F("quantity"))
        .values("id")
    )
    return queryset.filter(Q(id__in=inactive_candidates) | Q(id__in=inactive_out_of_stock))


def make_room_specific_query(room) -> QuerySet:
    return Q(rooms__id=room) | Q(rooms=None)


def make_unprocessed_signups_query() -> QuerySet:
    from stregsystem.models import PendingSignup, ApprovalModel

    return PendingSignup.objects.filter(status__exact=ApprovalModel.UNSET)


def unprocessed_mobilepayments_filter() -> Q:
    from stregsystem.models import ApprovalModel

    return Q(payment__isnull=True) & Q(status__exact=ApprovalModel.UNSET)


def make_unprocessed_mobilepayment_query() -> QuerySet:
    from stregsystem.models import MobilePayment  # import locally to avoid circular import

    return MobilePayment.objects.filter(unprocessed_mobilepayments_filter()).order_by('-timestamp')


def make_processed_mobilepayment_query() -> QuerySet:
    from stregsystem.models import MobilePayment  # import locally to avoid circular import

    return MobilePayment.objects.filter(
        Q(payment__isnull=True)
        & Q(member__isnull=False)
        & Q(status__in=[MobilePayment.APPROVED, MobilePayment.IGNORED])
    )


def make_unprocessed_member_filled_mobilepayment_query() -> QuerySet:
    from stregsystem.models import MobilePayment  # import locally to avoid circular import

    return MobilePayment.objects.filter(
        unprocessed_mobilepayments_filter() & Q(amount__gte=5000) & Q(member__isnull=False)
    )


def make_unprocessed_membership_payment_query() -> QuerySet:
    from stregsystem.models import MobilePayment

    return MobilePayment.objects.filter(
        unprocessed_mobilepayments_filter()
        & Q(member__isnull=True)
        & Q(comment__regex=r'^signup:[0-9a-fA-F-]{36}\+.{1,16}$')
    )


def date_to_midnight(date):
    """
    Converts a datetime.date to a datetime of the same date at midnight.

    :param date: date to convert
    :return: the date as a timezone aware datetime at midnight
    """
    return timezone.make_aware(timezone.datetime(date.year, date.month, date.day, 0, 0))


def parse_csv_and_create_mobile_payments(csv_file):
    imported_transactions, duplicate_transactions = 0, 0
    import csv

    # get csv reader and ignore header
    reader = csv.reader(csv_file[1:], delimiter=';', quotechar='"')
    for row in reader:
        from stregsystem.models import MobilePayment

        mobile_payment = MobilePayment(
            member=None,
            amount=row[2].replace(',', ''),
            timestamp=parse_datetime(row[3]),
            customer_name=row[4],
            transaction_id=row[7],
            comment=row[6],
            payment=None,
        )
        try:
            # unique constraint on transaction_id and payment-foreign key must hold before saving new object
            mobile_payment.validate_unique()

            # do case insensitive exact match on active members
            mobile_payment.member = mobile_payment_exact_match_member(mobile_payment.comment)
            mobile_payment.save()
            imported_transactions += 1
        except ValidationError:
            duplicate_transactions += 1
    return imported_transactions, duplicate_transactions


def mobile_payment_exact_match_member(comment):
    from stregsystem.models import Member

    match = Member.objects.filter(username__iexact=comment.strip(), active=True)
    if match.count() == 1:
        return match.get()
    elif match.count() > 1:
        # something is very wrong, there should be no active users which are duplicates post PR #178
        raise RuntimeError("Duplicate usernames found at MobilePayment import. Should not exist post PR #178")


def strip_emoji(text):
    # allowlist decided by string.printables and all unique chars from usernames
    return re.sub(
        '[^a-zA-Z0-9äåæéëöø!"#$%&()*+,\-_./:;<=>?@\\\^`\]{|}~£§¶Ø\s]',
        '',
        text,
    ).strip()


def qr_code(data) -> HttpResponse:
    response = HttpResponse(content_type="image/svg+xml")
    qr = qrcode.make(data, image_factory=qrcode.image.svg.SvgPathFillImage)
    qr.save(response)

    return response


def mobilepay_launch_uri(comment: str, amount: float) -> str:
    query = {'phone': '90601', 'comment': comment}

    if amount is not None:
        query['amount'] = amount

    return 'mobilepay://send?{}'.format(urllib.parse.urlencode(query))


class stregsystemTestRunner(DiscoverRunner):
    def __init__(self, *args, **kwargs):
        settings.TEST_MODE = True
        super(stregsystemTestRunner, self).__init__(*args, **kwargs)


class PaymentToolException(RuntimeError):
    """
    Structured exception for runtime error due to race condition during submission of Paymenttool form
    """

    def __init__(self, racy_mbpayments: QuerySet):
        self.racy_mbpayments = racy_mbpayments
        self.inconsistent_mbpayments_count = self.racy_mbpayments.count()
        self.inconsistent_transaction_ids = [x.transaction_id for x in self.racy_mbpayments]


class fakefile:
    data = ""

    def write(self, data):
        self.data += data


# little function to make sure the csv data always has the same format
def rows_to_csv(rows) -> str:
    file = fakefile()
    # Converting elements in rows to strings to ensure it can be written to the file object
    csv.writer(file).writerows([[str(item) for item in row] for row in rows])
    return file.data


def get_member_rankings_current_year(member):
    now = timezone.now()
    from_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    to_date = now
    return get_member_rankings(member, from_date, to_date)


def get_member_rankings_current_month(member):
    now = timezone.now()
    from_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    to_date = now
    return get_member_rankings(member, from_date, to_date)


def get_product_ids_for_category(category: Category) -> list[int]:
    return list(Product.objects.filter(categories=category).values_list('id', flat=True))


def get_category_product_ids(categories: list[Category]) -> dict[Category, list[int]]:
    return {category: get_product_ids_for_category(category) for category in categories}


def ranking(
    member: Member, product_ids: list[int], from_date: datetime.datetime, to_date: datetime.datetime
) -> tuple[int, int]:
    qs = (
        Member.objects.filter(
            sale__product__in=product_ids,
            sale__timestamp__gt=from_date,
            sale__timestamp__lte=to_date,
        )
        .annotate(Count('sale'))
        .order_by('-sale__count', 'username')
    )
    if member not in qs:
        return 0, qs.count()
    rank = list(qs).index(Member.objects.get(id=member.pk)) + 1
    return rank, qs.count()


def category_per_uni_day(
    member: Member, product_ids: list[int], from_date: datetime.datetime, to_date: datetime.datetime
) -> str:
    qs = Member.objects.filter(
        id=member.pk,
        sale__product__in=product_ids,
        sale__timestamp__gt=from_date,
        sale__timestamp__lte=to_date,
    )
    if member not in qs:
        return "0.00"
    university_days = (to_date - from_date).days * 162.14 / 365  # university workdays in 2021
    return "{:.2f}".format(qs.count() / university_days)


def sale_count_for_product(
    member: Member, product_ids: list[int], from_date: datetime.datetime, to_date: datetime.datetime
) -> int:
    return Sale.objects.filter(
        member=member,
        product__in=product_ids,
        timestamp__gt=from_date,
        timestamp__lte=to_date,
    ).count()


def get_member_rankings(
    member: Member, from_date: datetime.datetime, to_date: datetime.datetime
) -> dict[Category, tuple[tuple[int, int], str, int]]:
    category_product_ids = get_category_product_ids(list(Category.objects.all()))

    return {
        category: (
            ranking(member, product_ids, from_date, to_date),
            category_per_uni_day(member, product_ids, from_date, to_date),
            sale_count_for_product(member, product_ids, from_date, to_date),
        )
        for category, product_ids in category_product_ids.items()
    }
