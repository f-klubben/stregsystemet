import smtplib
import logging


from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


logger = logging.getLogger(__name__)

def send_email(mailadress, msg_string):
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
            Hej {member.firstname}!
            Velkommen som fember i Fklubben.
            Du har nu en brugerkonto oprettet. Dit brugernavn er {member.username}. 

            De 200 kr du har givet for at blive medlem betaler for din adgang til fredagsfranskbrød, hver onsdag.
            Når du møder op til fredagsfranskbrød, så kan du opleve en razzia. Her skriver du dit brugernavn ind ({member.username}), for at sikre at du er medlem af fklubben.

            Med dit brugernavn kan du også købe drikkevarer fra strandvejen.
            Bemærk at du skal indsætte penge på din stregkonto før at du kan købe noget på strandvejen.
            Dette kan gøres ved at sende en yderligere betaling på MobilePay til Fklubben, med det beløb som du gerne vil have indsat.
            Priserne kan ses i stegsystemet på strandvejen. 


            Mvh,<br>
            TREOen
        </body>
    </html>
    """
    

    
    msg.attach(MIMEText(html, 'html'))
    send_email(member.email, msg.as_string())
