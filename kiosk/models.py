import random
from django.utils import timezone
from .validators import validate_file_extension, valid_images
from django.db import models
from django.core.validators import MinValueValidator
import os


def random_ordering():
    return random.randint(1, 1000)


class KioskItem(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True, unique=False)
    notes = models.CharField(max_length=2000, blank=True, null=True)
    uploaded_date = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)
    media = models.FileField(upload_to='kiosk', blank=True, validators=[validate_file_extension])
    website_url = models.URLField(blank=True)
    ordering = models.IntegerField(null=False, default=random_ordering, blank=False)
    start_datetime = models.DateTimeField(null=True, blank=True)
    end_datetime = models.DateTimeField(null=True, blank=True)
    duration = models.IntegerField(
        null=False, default=10000, blank=False, validators=[MinValueValidator(1000)], verbose_name="Duration (ms)"
    )

    @property
    def has_media(self):
        return bool(self.media)

    @property
    def is_image(self):
        name, extension = os.path.splitext(self.media.name)
        return extension in valid_images
