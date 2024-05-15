import smtplib
import logging
import csv


from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import escape
from django.utils import timezone
from stregsystem.templatetags.stregsystem_extras import money

logger = logging.getLogger(__name__)


def send_welcome_mail(member):
    send_template_mail(
        member,
        "welcome.html",
        {**vars(member), 'formatted_balance': money(member.balance)},
        None,  # Original code didn't specify a subject line.
    )


def send_payment_mail(member, amount, mobilepay_comment):
    send_template_mail(
        member,
        "deposit_manual.html" if mobilepay_comment else "deposit_automatic.html",
        {**vars(member), 'formatted_amount': money(amount), 'mobilepay_comment': escape(mobilepay_comment)},
        "Stregsystem payment",
    )


data_sent = {}


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


def send_userdata_mail(member):
    from .models import Payment, Sale, MobilePayment

    now = timezone.now()
    td = now - timezone.timedelta(minutes=5)
    if member.id in data_sent.keys() and data_sent[member.id] > td:
        return False
    data_sent[member.id] = now

    sales: list[Sale] = member.sale_set.order_by("timestamp")
    payments: list[Payment] = member.payment_set.order_by("timestamp")
    mobilepayments: list[MobilePayment] = member.mobilepayment_set.order_by("timestamp")
    mobilepay_payments: list[Payment] = [mobilepayment.payment for mobilepayment in mobilepayments]

    sales_csv = rows_to_csv(
        [["Timestamp", "Name", "Price"]] + [[sale.timestamp, sale.product.name, sale.price] for sale in sales]
    )
    payments_csv = rows_to_csv(
        [["Timestamp", "Amount", "Is Mobilepay"]]
        + [[payment.timestamp, payment.amount, payment in mobilepay_payments] for payment in payments]
    )
    userdata_csv = rows_to_csv(
        [
            ["Id", "Name", "First name", "Last name", "Email", "Registration year"],
            [member.id, member.username, member.firstname, member.lastname, member.email, member.year],
        ]
    )

    send_template_mail(
        member,
        "send_csv.html",
        {**vars(member), "fember": member.username},
        f'{member.username} has requested their user data!',
        {"sales.csv": sales_csv.encode(), "payments.csv": payments_csv.encode(), "userdata.csv": userdata_csv.encode()},
    )
    member.save()
    return True


def send_template_mail(member, target_template: str, context: dict, subject: str, attachments: dict = {}):
    msg = MIMEMultipart()
    msg['From'] = 'treo@fklub.dk'
    msg['To'] = member.email
    msg['Subject'] = subject
    html = render_to_string(f"mail/{target_template}", context)
    msg.attach(MIMEText(html, 'html'))

    if hasattr(settings, 'TEST_MODE'):
        return

    for name, attachment in attachments.items():
        attachment = MIMEApplication(attachment, Name=name)
        attachment['Content-Disposition'] = f'attachment; filename={name}'
        msg.attach(attachment)

    try:
        smtpObj = smtplib.SMTP('localhost', 25)
        smtpObj.sendmail('treo@fklub.dk', member.email, msg.as_string())
    except Exception as e:
        logger.error(str(e))
