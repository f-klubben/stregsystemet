import random

from django.db import models
from polymorphic.models import PolymorphicModel


def random_ordering():
    return random.randint(1, 1000)

def validate_video_file(file):
    if not file.name.endswith('.mp4'):
        raise ValueError("Uploaded file must be a mp4 video file")


class KioskItem(PolymorphicModel):
    name = models.CharField(max_length=100, blank=True, null=True, unique=False)
    notes = models.CharField(max_length=2000, blank=True, null=True)
    uploaded_date = models.DateField(auto_now_add=True)
    active = models.BooleanField(default=True)
    ordering = models.IntegerField(null=False, default=random_ordering, blank=False)
    duration = models.IntegerField(null=False, default=10, blank=False)

    def getTemplate(self):
        return None

class KioskImage(KioskItem):
    image = models.ImageField(upload_to='kiosk', null=False)

    def getTemplate(self):
        return "kioskImage.html"

class KioskVideo(KioskItem):
    video = models.FileField(upload_to='kiosk', null=False, validators=[validate_video_file])

    def getTemplate(self):
        return "kioskVideo.html"
