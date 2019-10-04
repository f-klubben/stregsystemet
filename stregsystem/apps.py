from django.apps import AppConfig

from django.db.models.signals import post_save

class StregConfig(AppConfig):
    name = 'stregsystem'

    def ready(self):
        from .models import Member
        from stregsystem.signals import after_member_save
        post_save.connect(after_member_save, sender=Member)
