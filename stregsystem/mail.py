import smtplib
import logging


from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from .utils import money
from django.conf import settings 


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
    html = f"""
    <html>
        <head></head>
        <body>
            Hej {member.firstname}!<br><br>
            Velkommen som fember (medlem) i Fklubben!
            Din stregkonto (bruger) er oprettet med følgende brugernavn: <b>{member.username}</b>.<br>
            Fremover kan du benytte dit brugernavn i <a href="http://fklub.dk/treo/stregsystem">stregsystemet</a> til køb af diverse varer og/eller event billetter, såfremt du har penge på din stregkonto.<br>
            Din nuværende saldo er: {money(member.balance)} kr.<br><br>
            Hvis du har nogen spørgsmål henviser vi til <a href="http://fklub.dk">fklub.dk</a>, men ellers er du meget velkommen til at kontakte os på <a href="mailto:info@fklub.dk">info@fklub.dk</a> eller <a href="https://www.facebook.com/fklub">Facebook</a>.<br><br>

			Følg med på <a href="https://www.facebook.com/fklub">Facebook</a> og <a href="https://www.instagram.com/fklub">Instagram</a> for events, billeder, og andre relevante indslag.<br><br>
			Husk at der er fredagsfranskbrød i kantinen hver onsdag kl. 10.00!<br><br> 
            Med venlig hilsen,<br>
            F-klubben
        </body>
    </html>
    """
    

    
    msg.attach(MIMEText(html, 'html'))
    send_email(member.email, msg.as_string())
