import smtplib
import logging


from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from .utils import money


logger = logging.getLogger(__name__)

def send_email(mailadress, msg_string):
    try:
        smtpObj = smtplib.SMTP('localhost', 25)
        smtpObj.sendmail('treo@fklub.dk', mailadress, msg_string)
    except Exception as e:
        logger.error(str(e))


def send_welcome_mail(member):
    msg = MIMEMultipart()
    
    if member.balance != 0:
        balancemsg = f"""Din stregkonto har en balance på {money(member.balance)}"""
    else:
        balancemsg = f"""Bemærk at du skal indsætte penge på din stregkonto før at du kan købe noget på strandvejen.<br>
        Dette kan gøres ved at sende en yderligere betaling på MobilePay til Fklubben, med det beløb som du gerne vil have indsat."""
    
    html = f"""
    <html>
        <head></head>
        <body>
            Hej {member.firstname}!<br><br>
            Velkommen som fember i Fklubben.
            Du har nu en brugerkonto oprettet. Dit brugernavn er {member.username}.<br><br>

            De 200 kr du har givet for at blive medlem betaler for din adgang til fredagsfranskbrød, hver onsdag.<br><br>

            Med dit brugernavn kan du også købe drikkevarer fra Strandvejen. 
            Strandvejen er det lille køkken i klynge 2, stueetagen, nær Jægerstuen med de fire køleskabe og stregsystemets terminal.<br>
            {balancemsg}<br>
            Priserne kan ses i stegsystemet på strandvejen.<br><br><br>


            Mvh,<br>
            TREOen
        </body>
    </html>
    """
    

    
    msg.attach(MIMEText(html, 'html'))
    send_email(member.email, msg.as_string())
