# -*- coding: utf8 -*-
import pprint

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client

from kiosk.models import KioskItem

try:
    from unittest.mock import patch, MagicMock, Mock
except ImportError:
    from mock import patch, MagicMock, Mock


class KioskTests(TestCase):
    def test_kiosk_empty(self):
        c = Client()
        response = c.get('/kiosk/next')
        self.assertEqual(404, response.status_code)

    def kiosk_one_item(self, mode):
        image_path = "media/kiosk/test_image.png"
        image = SimpleUploadedFile(name='test_image.png',
                                   content=open(image_path, 'rb').read(),
                                   content_type='image/jpeg')
        KioskItem.objects.create(name="testkiosk", image=image, active=True)

        self.assertEqual(1, KioskItem.objects.count())

        c = Client()
        response = c.get('/kiosk/{}'.format(mode))
        self.assertEqual(200, response.status_code)

        # Django generates a random string to add to the filename
        self.assertIn(b'/media/kiosk/test_image_', response.content)

    def test_kiosk_one_item_mode_next(self):
        self.kiosk_one_item("next")

    def test_kiosk_one_item_mode_random(self):
        self.kiosk_one_item("random")

    def kiosk_two_items(self, mode):
        image_path = "media/kiosk/test_image.png"
        image = SimpleUploadedFile(name='test_image1.png',
                                   content=open(image_path, 'rb').read(),
                                   content_type='image/jpeg')
        KioskItem.objects.create(name="testkiosk1", image=image, active=True)

        image_path = "media/kiosk/test_image.png"
        image = SimpleUploadedFile(name='test_image2.png',
                                   content=open(image_path, 'rb').read(),
                                   content_type='image/jpeg')
        KioskItem.objects.create(name="testkiosk2", image=image, active=True)

        self.assertEqual(2, KioskItem.objects.count())

        c = Client()
        response = c.get('/kiosk/{}'.format(mode))
        self.assertEqual(200, response.status_code)

        # Django generates a random string to add to the filename
        self.assertIn(b'/media/kiosk/test_image', response.content)

    def test_kiosk_two_items_mode_next(self):
        self.kiosk_two_items("next")

    def test_kiosk_two_items_mode_random(self):
        self.kiosk_two_items("random")
