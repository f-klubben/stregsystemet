from django.db import models
import random


def random_ordering():
    return random.randint(1, 1000)


class KioskItem(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True, unique=False)
    notes = models.CharField(max_length=2000, blank=True, null=True)
    uploaded_date = models.DateField(auto_now_add=True)
    active = models.BooleanField(default=True)
    image = models.ImageField(upload_to='kiosk', null=False)
    ordering = models.IntegerField(null=False, default=random_ordering, blank=False)
