from django.contrib.auth.models import User
from django.core.management import BaseCommand

from stregsystem.models import MobilePayment
from stregsystem.utils import make_unprocessed_member_filled_mobilepayment_query


def submit_filled_mobilepayments(user: User) -> int:
    """
    Count, approve, and submit MobilePayments.
    :param user: Admin user
    :return: Count of processed mobile payments
    """
    before_count = MobilePayment.objects.filter(status=MobilePayment.APPROVED).count()

    MobilePayment.approve_member_filled_mobile_payments()
    MobilePayment.submit_processed_mobile_payments(user)

    return MobilePayment.objects.filter(status=MobilePayment.APPROVED).count() - before_count


class Command(BaseCommand):
    help = "Run mobilepayment matching and insert exact matches automatically"

    def handle(self, *args, **options):
        # if no payments to be processed exists, stop job
        if make_unprocessed_member_filled_mobilepayment_query().count() == 0:
            self.stdout.write(self.style.NOTICE("[autopayment] No payments to be auto-processed"))
            return

        # if logging user does not exist, stop job
        if User.objects.filter(username="autopayment").exists():
            auto_user = User.objects.get(username="autopayment")
        else:
            self.stdout.write(self.style.ERROR("[autopayment] No user 'autopayment' exists, cannot do autopayments."))
            return

        count = submit_filled_mobilepayments(auto_user)

        self.stdout.write(
            self.style.SUCCESS(f'[autopayment] Successfully submitted {count} mobilepayments automatically')
        )
