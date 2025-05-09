from django.db import models

from stregsystem.models import Member


class BreadRazzia(models.Model):
    class Meta:
        permissions = (("host_razzia", "Can host a foobar, fnugfald or bread razzia"),)

    BREAD = "BR"
    FOOBAR = "FB"
    FNUGFALD = "FF"
    RAZZIA_CHOICES = [
        (BREAD, "Brødrazzia"),
        (FOOBAR, "Foobar razzia"),
        (FNUGFALD, "Fnugfald razzia"),
    ]
    members = models.ManyToManyField(Member, through="RazziaEntryOld")
    start_date = models.DateTimeField(auto_now_add=True)
    razzia_type = models.CharField(max_length=2, choices=RAZZIA_CHOICES, default=BREAD)


class RazziaEntryOld(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    razzia = models.ForeignKey(BreadRazzia, on_delete=models.CASCADE)
    time = models.DateTimeField(null=True, blank=True, auto_now_add=True)
