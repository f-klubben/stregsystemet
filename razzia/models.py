from django.db import models

from stregsystem.models import Member
from datetime import timedelta


class Razzia(models.Model):
    class Meta:
        permissions = (("host_razzia", "Can host a foobar, fnugfald or bread razzia"),)

    name = models.CharField(max_length=20)
    turns_per_member = models.IntegerField(default=0)
    turn_interval = models.DurationField(default=timedelta(0))
    # required_products = models.ManyToManyField(Product)
    # purchase_start_date = models.DateTimeField(null=True, blank=True)
    # purchase_end_date = models.DateTimeField(null=True, blank=True)

    members = models.ManyToManyField(Member, through='RazziaEntry')
    start_date = models.DateTimeField(auto_now_add=True)


class RazziaEntry(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    razzia = models.ForeignKey(Razzia, on_delete=models.CASCADE)
    time = models.DateTimeField(null=True, blank=True, auto_now_add=True)
