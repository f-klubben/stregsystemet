from __future__ import unicode_literals

from django.db import models


class KioskItem(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True, unique=False)
    notes = models.CharField(max_length=2000, blank=True, null=True)
    uploaded_date = models.DateField(auto_now_add=True)
    active = models.BooleanField(default=True)
    image = models.ImageField(upload_to='kiosk', null=False)
