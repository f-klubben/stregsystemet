import random
from django.utils import timezone
from .validators import validate_file_extension, valid_images
from django.db import models
import os


def random_ordering():
    return random.randint(1, 1000)


class KioskItem(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True, unique=False)
    notes = models.CharField(max_length=2000, blank=True, null=True)
    uploaded_date = models.DateField(auto_now_add=True)
    active = models.BooleanField(default=True)
    media = models.FileField(upload_to='kiosk', null=False, validators=[validate_file_extension])
    ordering = models.IntegerField(null=False, default=random_ordering, blank=False)
    start_datetime = models.DateTimeField(default=timezone.now(), blank=True)
    end_datetime = models.DateTimeField(null=True, blank=True)

    @property
    def is_image(self):
        name, extension = os.path.splitext(self.media.name)
        return extension in valid_images

    def is_active_period(self, current_time) -> bool:
        return (self.start_datetime < current_time) and (self.end_datetime is None or self.end_datetime > current_time)
