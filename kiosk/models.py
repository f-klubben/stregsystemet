from __future__ import unicode_literals

from django.conf import settings
from django.db import models

# Create your models here.
class KioskItem(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True, unique=False)
    #description = models.CharField(max_length=2000)
    #uploadedDate = models.DateField(auto_now_add=True)
    active = models.BooleanField(default=True)
    image = models.ImageField(upload_to = 'kiosk', null=False)