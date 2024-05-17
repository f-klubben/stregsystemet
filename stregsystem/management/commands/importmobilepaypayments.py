from datetime import timedelta, date

from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime

from requests import HTTPError

from stregsystem.models import MobilePayment
import logging

from stregsystem.utils import mobile_payment_exact_match_member, strip_emoji

from stregsystem.vipps_api import AccountingAPI


class Command(BaseCommand):
    help = 'Imports the latest payments from MobilePay'

    # Cutoff for when this iteration of the Mobilepay-API (Vipps) is deployed
    manual_cutoff_date = date(2024, 4, 9)

    logger = logging.getLogger(__name__)
    days_back = None

    def add_arguments(self, parser):
        parser.add_argument(
            'days_back',
            nargs='?',
            type=int,
            default=7,
            help="Days back from today to look for MobilePay transactions (max 31 days)",
        )

    def handle(self, *args, **options):
        self.days_back = options['days_back'] if options['days_back'] <= 31 else 7
        self.import_mobilepay_payments()

    def fetch_transactions(self) -> list:
        # Do a client side check if token is good. If not - fetch another token.
        try:
            assert self.days_back is not None

            transactions = []

            transactions.extend(AccountingAPI.get_transactions_latest_feed())

            for i in range(self.days_back):
                past_date = date.today() - timedelta(days=i)
                if past_date < self.manual_cutoff_date:
                    break

                transactions.extend(AccountingAPI.get_transactions_historic(past_date))

            return transactions
        except HTTPError as e:
            self.logger.error(f"Got an HTTP error when trying to fetch transactions: {e.response}")
        except Exception as e:
            self.logger.error(f'Got an error when trying to fetch transactions: {e}')

    def import_mobilepay_payments(self):
        transactions = self.fetch_transactions()
        if len(transactions) == 0:
            self.logger.info(f'Ran, but no transactions found')
            return

        for transaction in transactions:
            self.import_mobilepay_payment(transaction)

        self.logger.info('Successfully ran MobilePayment API import')

    def import_mobilepay_payment(self, transaction):
        """
        Example of a transaction:
        {
            "pspReference": "32212390715",
            "time": "2024-04-05T07:19:26.528092Z",
            "ledgerDate": "2024-04-05",
            "entryType": "capture",
            "reference": "10113143347",
            "currency": "DKK",
            "amount": 20000,
            "recipientHandle": "DK:90601",
            "balanceAfter": 110000,
            "balanceBefore": 90000,
            "name": "Jakob Topper",
            "maskedPhoneNo": "xxxx 1234",
            "message": "Topper"
        }
        :param transaction:
        :return:
        """
        if transaction['entryType'] != 'capture':
            return

        payment_datetime = parse_datetime(transaction['time'])

        if payment_datetime.date() < self.manual_cutoff_date:
            self.logger.debug(f'Skipping transaction because it is before payment cutoff date {payment_datetime}')
            return

        trans_id = transaction['pspReference']

        if MobilePayment.objects.filter(transaction_id=trans_id).exists():
            self.logger.debug(f'Skipping transaction since it already exists (PSP-Reference: {trans_id})')
            return

        currency_code = transaction['currency']
        if currency_code != 'DKK':
            self.logger.warning(f'Does ONLY support DKK (Transaction ID: {trans_id}), was {currency_code}')
            return

        amount = transaction['amount']

        comment = strip_emoji(transaction['message'])
        name = transaction['name']  # Danish legal name, no reason to sanitize.

        MobilePayment.objects.create(
            amount=amount,  # already in streg-ører
            member=mobile_payment_exact_match_member(comment),
            comment=comment,
            customer_name=name,
            timestamp=payment_datetime,
            transaction_id=trans_id,
            status=MobilePayment.UNSET,
        )

        self.logger.info(f'Imported transaction id: {trans_id} for amount: {amount}')
