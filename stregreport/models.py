from django.db import models

from stregsystem.models import Member


class BreadRazzia(models.Model):
    members = models.ManyToManyField(Member)
    start_date = models.DateTimeField(auto_now_add=True)
