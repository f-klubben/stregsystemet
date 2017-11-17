from __future__ import unicode_literals

from django.db import models
import random
from polymorphic.models import PolymorphicModel


def random_ordering():
    return random.randint(1, 1000)


class KioskItem(PolymorphicModel):
    name = models.CharField(max_length=100, blank=True, null=True, unique=False)
    notes = models.CharField(max_length=2000, blank=True, null=True)
    uploaded_date = models.DateField(auto_now_add=True)
    active = models.BooleanField(default=True)
    ordering = models.IntegerField(null=False, default=random_ordering, blank=False)

    def getContent(self):
        pass

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.__str__()

class KioskImageItem(KioskItem):
    image = models.ImageField(upload_to='kiosk', null=False)

    def getContent(self):
        return self.image.url

class KioskWebsiteItem(KioskItem):
    url = models.CharField(max_length=2048, blank=False, null=False, unique=False)

    def getContent(self):
        return self.url