
from django.db.models.signals import post_save
from django.db.models import F
from django.dispatch import receiver

def after_member_save(sender, instance, created, **kwargs):
    
    from .mail import send_welcome_mail
    if sender.__name__ != "Member":
        return
    if not created:
        return
    
    send_welcome_mail(instance)