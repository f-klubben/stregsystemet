from django.test import TestCase
from django.urls import reverse
from mock import patch, MagicMock

class SaleViewTests(TestCase):
    fixtures = ["initial_data"]

    @patch('stregsystem.models.Member.make_sale')
    def test_make_sale_number_quickbuy_success(self, make_sale):
        response = self.client.post(reverse('sale', args=(1, )), {"quickbuy": "jokke 1"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "stregsystem/index_sale.html")
        make_sale.assert_called_once_with(900)

    def test_make_sale_stregforbud_quickbuy_fail(self):
        response = self.client.post(reverse('sale', args=(1, )), {"quickbuy": "jan 1"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "stregsystem/error_stregforbud.html")
