from django.apps import AppConfig

from django.db.models.signals import post_save
from stregsystem.signals import after_member_save, after_pending_signup_save, after_intent_save


class StregConfig(AppConfig):
    name = 'stregsystem'

    def ready(self):
        from stregsystem.models import Member, PendingSignup, Intent

        post_save.connect(after_member_save, sender=Member)
        post_save.connect(after_pending_signup_save, sender=PendingSignup)
        post_save.connect(after_intent_save, sender=Intent)
