import smtplib
import logging


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


def send_csv_mail(member):
    now = timezone.now()
    if member.requested_data_time is not None:
        ten_minutes_ago = now - timezone.timedelta(minutes=10)
        if member.requested_data_time > ten_minutes_ago:
            return False
        else:
            member.requested_data_time = now
    else:
        member.requested_data_time = now

    # haha linting as i have no idea how django works otherwise
    from .models import Payment, Sale

    sales: list[Sale] = member.sale_set.order_by("timestamp")
    payments: list[Payment] = member.payment_set.order_by("timestamp")

    sales_csv = "Name, Price, Timestamp\n"
    sales_csv += "\n".join([f'{sale.product.name},{sale.price},{sale.timestamp}' for sale in sales])
    payments_csv = "Timestamp, Amount\n"
    payments_csv += "\n".join([f'{payment.timestamp},{payment.amount}' for payment in payments])
    userdata_csv = "Id, Name, First name, Last name, Email, Registration year\n"
    userdata_csv += f"{member.id},{member.username},{member.firstname},{member.lastname},{member.email},{member.year}"

    send_template_mail(
        member,
        "send_csv.html",
        {**vars(member), "fember": member.username},
        f'{member.username} has requested their user data!',
        {"sales.csv": sales_csv, "payments.csv": payments_csv, "userdata.csv": userdata_csv},
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
