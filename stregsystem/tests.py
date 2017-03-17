from django.test import TestCase
from django.urls import reverse
from mock import patch, MagicMock

from .models import PayTransaction

class SaleViewTests(TestCase):
    fixtures = ["initial_data"]

    def test_make_sale_letter_quickbuy(self):
        response = self.client.post(reverse('quickbuy', args="1"), {"quickbuy": "jokke a"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("stregsystem/error_invalidinput.html")

    @patch('stregsystem.models.Member.can_fulfill')
    @patch('stregsystem.models.Member.fulfill')
    def test_make_sale_quickbuy_success(self, fulfill, can_fulfill):
        can_fulfill.return_value = True

        response = self.client.post(reverse('quickbuy', args=(1, )), {"quickbuy": "jokke 1"})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "stregsystem/index_sale.html")

        (args, kwargs) = fulfill.call_args
        (last_trans, ) = args
        self.assertEqual(last_trans, PayTransaction(900))

    @patch('stregsystem.models.Member.can_fulfill')
    @patch('stregsystem.models.Member.fulfill')
    def test_make_sale_quickbuy_fail(self, fulfill, can_fulfill):
        can_fulfill.return_value = False

        response = self.client.post(reverse('quickbuy', args=(1, )), {"quickbuy": "jan 1"})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "stregsystem/error_stregforbud.html")

        fulfill.assert_not_called()

    @patch('stregsystem.models.Member.can_fulfill')
    @patch('stregsystem.models.Member.fulfill')
    def test_make_sale_menusale_fail(self, fulfill, can_fulfill):
        can_fulfill.return_value = False

        response = self.client.get(reverse('menu_sale', args=(1, 1, 1)))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "stregsystem/error_stregforbud.html")

        fulfill.assert_not_called()

    @patch('stregsystem.models.Member.can_fulfill')
    @patch('stregsystem.models.Member.fulfill')
    def test_make_sale_menusale_success(self, fulfill, can_fulfill):
        can_fulfill.return_value = True

        response = self.client.get(reverse('menu_sale', args=(1, 1, 1)))
        self.assertTemplateUsed(response, "stregsystem/menu.html")

        self.assertEqual(response.status_code, 200)

        (args, kwargs) = fulfill.call_args
        (last_trans, ) = args
        self.assertEqual(last_trans, PayTransaction(900))
