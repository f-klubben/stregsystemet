from django.db.models.signals import post_save
from django.db.models import F
from django.dispatch import receiver


def after_member_save(sender, instance, created, **kwargs):
    if sender.__name__ != "Member":
        return
    if not created:
        return

    instance.trigger_welcome_mail()


def after_pending_signup_save(sender, instance, created, **kwargs):
    if sender.__name__ != "PendingSignup":
        return

    instance.member.trigger_welcome_mail()

    from stregsystem.models import ApprovalModel
    if instance.status == ApprovalModel.APPROVED and instance.member.signup_due_paid:
        instance.delete()
