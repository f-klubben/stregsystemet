import smtplib
import logging


from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from .utils import money
from django.conf import settings
from django.template.loader import render_to_string


logger = logging.getLogger(__name__)


def send_email(mailadress, msg_string):
    if hasattr(settings, 'TEST_MODE'):
        return
    try:
        smtpObj = smtplib.SMTP('localhost', 25)
        smtpObj.sendmail('treo@fklub.dk', mailadress, msg_string)
    except Exception as e:
        logger.error(str(e))


def send_welcome_mail(member):
    msg = MIMEMultipart()

    context = dict()
    context.update(vars(member))
    context.update({'money_result': money(member.balance)})

    html = render_to_string("message_templates/welcome.html", context)

    msg.attach(MIMEText(html, 'html'))
    send_email(member.email, msg.as_string())
