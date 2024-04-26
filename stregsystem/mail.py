import smtplib
import logging
from datetime import datetime, timedelta


from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import escape
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


def send_template_mail(member, target_template: str, context: dict, subject: str):
    msg = MIMEMultipart()
    msg['From'] = 'treo@fklub.dk'
    msg['To'] = member.email
    msg['Subject'] = subject
    html = render_to_string(f"mail/{target_template}", context)
    msg.attach(MIMEText(html, 'html'))

    if hasattr(settings, 'TEST_MODE'):
        return

    try:
        smtpObj = smtplib.SMTP('localhost', 25)
        smtpObj.sendmail('treo@fklub.dk', member.email, msg.as_string())
    except Exception as e:
        logger.error(str(e))

users_who_has_requested:dict[int,datetime] = {}

def send_csv_mail(member):
    global users_who_has_requested

    if member.id in users_who_has_requested.keys():
        now = datetime.now()
        ten_days_ago = now  - timedelta(days=10)
        if users_who_has_requested[member.id] > ten_days_ago:
            return False

    # haha linting as i have no idea how django works otherwise
    from .models import Payment, Sale
    sales:list[Sale] = member.sale_set.order_by("-timestamp")
    payments:list[Payment] = member.payment_set.order_by("-timestamp")

    sales_csv = "Name, Price, Timestamp"
    sales_csv += "\n".join([f'{sale.product.name},{sale.price},{sale.timestamp}' for sale in sales])
    payments_csv = "Timestamp, Amount"
    payments_csv += "\n".join([f'{payment.timestamp},{payment.amount}' for payment in payments])
    userdata_csv = "Id, Name, First name, Last name, Email, Registration year"
    userdata_csv += f"{member.id},{member.username},{member.firstname},{member.lastname},{member.email},{member.year}"

    msg = MIMEMultipart()
    msg['From'] = 'treo@fklub.dk'
    msg['To'] = member.email
    msg['Subject'] = f'[TREO] {member.username} user data request'
    msg.attach(MIMEText(render_to_string("mail/send_csv.html", {
        "fember":member.username
    }), 'html'))
    for name, csv in {"sales": sales_csv, "payments":payments_csv, "userdata":userdata_csv}.items():
        attachment = MIMEApplication(csv, Name=f"{name}.csv")
        attachment['Content-Disposition'] = f'attachment; filename="{name}.csv"'
        msg.attach(attachment)
    
    try:
        smtpObj = smtplib.SMTP('localhost', 25)
        smtpObj.sendmail('treo@fklub.dk', member.email, msg.as_string())
    except Exception as e:
        logger.error(str(e))
    return True