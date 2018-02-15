# -*- coding: utf8 -*-

from django.test import TestCase, Client


class KioskTests(TestCase):
    def test_kiosk_empty(self):
        c = Client()
        response = c.get('/kiosk/next_real')
        self.assertEqual(404, response.status_code)
