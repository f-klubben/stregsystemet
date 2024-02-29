def after_member_save(sender, instance, created, **kwargs):
    from .mail import send_welcome_mail

    if sender.__name__ != "Member":
        return
    if not created:
        return

    send_welcome_mail(instance)
