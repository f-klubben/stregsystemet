import re
import uuid
from typing import Optional, Tuple

from django.core.management import BaseCommand
from django.utils.timezone import now

from stregsystem.utils import make_unprocessed_membership_payment_query
from stregsystem.models import MobilePayment, Payment, PendingSignup


def scan_comment(payment: MobilePayment) -> Optional[Tuple[uuid.UUID, str]]:
    match = re.match(r"^signup:(?P<token>[0-9a-fA-F-]{36})\+(?P<username>.{1,16})$", payment.comment)
    return (uuid.UUID(match.groups()[0]), match.groups()[1]) if match is not None else None


class Command(BaseCommand):
    help = 'Process transactions for automatic membership signup'

    def handle(self, *args, **options):
        unprocessed_payments = make_unprocessed_membership_payment_query().all()
        if len(unprocessed_payments) == 0:
            self.stdout.write(self.style.NOTICE("[autosignup] No membership payment transactions to be processed"))
            return

        signup_info = [scan_comment(p) for p in unprocessed_payments]

        for (index, payment) in enumerate(unprocessed_payments):
            payment: MobilePayment

            # This should not be possible since the db query already checks
            # the comment format...
            if signup_info[index] is None:
                raise RuntimeError("Invalid signup info found.")

            info: (uuid.UUID, str) = signup_info[index]

            try:
                signup = PendingSignup.objects.get(token=info[0])
            except PendingSignup.DoesNotExist:
                self.stdout.write(self.style.NOTICE("[autosignup] Payment for non-existing signup found"))
                continue

            signup.due -= payment.amount
            payment.status = MobilePayment.APPROVED

            # If their due has been payed activate the user and delete the signup object
            if signup.due <= 0:
                signup.complete(payment)
            else:
                signup.save(payment)




