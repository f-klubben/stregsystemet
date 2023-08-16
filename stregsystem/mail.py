import smtplib
import logging


from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import escape
from stregsystem.templatetags.stregsystem_extras import money

logger = logging.getLogger(__name__)


def send_welcome_mail(member):
    context = dict()
    context.update(vars(member))
    context.update({'formatted_balance': money(member.balance)})

    # Original code didn't specify a subject line.
    send_template_mail(member, "welcome.html", context, None)


def send_payment_mail(member, amount, mobilepay_comment):
    context = dict()
    context.update(vars(member))
    context.update({'formatted_amount': money(amount)})
    # TODO: not sure if escape serves any purpose here, since it's already being passed through a template.
    context.update({'mobilepay_comment': escape(mobilepay_comment)})

    target_template = "deposit_manual.html" if mobilepay_comment else "deposit_automatic.html"
    send_template_mail(member, target_template, context, "Stregsystem payment")


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
