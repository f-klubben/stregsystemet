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


def after_intent_save(sender, instance, created, **kwargs):
    """
    Notify potential webhooks/callbacks about state change.
    """
    if sender.__name__ != "Intent":
        return

    if not instance.webhook_url:
        return

    # Call the view internally to get the status response
    from django.test import RequestFactory
    from stregsystem.views import api_sale_intent_status

    factory = RequestFactory()
    request = factory.get('/')
    response = api_sale_intent_status(request, intent_id=instance.id)

    # Forward the response to the webhook
    import hmac
    import hashlib
    import requests

    # Sign the payload
    signature = hmac.new(
        key=str(instance.secret).encode(),
        msg=response.content,
        digestmod=hashlib.sha256,
    ).hexdigest()

    requests.post(
        instance.webhook_url,
        data=response.content,
        headers={
            "Content-Type": "application/json",
            "X-Webhook-Signature": f"sha256={signature}",
        },
    )
