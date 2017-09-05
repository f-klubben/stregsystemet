from django.test import TestCase
from django.urls import reverse


class SaleViewTests(TestCase):
    fixtures = ["initial_data"]

    def test_make_sale_letter_quickbuy(self):
        response = self.client.post(reverse('sale', args="1"), {"quickbuy": "jokke a"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("stregsystem/error_invalidinput.html")
