import datetime

from django.test import TestCase
from django.urls import reverse

from stregsystem import admin
from stregsystem.admin import ProductAdmin
from stregsystem.models import (GetTransaction, Member, PayTransaction,
                                StregForbudError, Product)

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch


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

        response = self.client.post(reverse('quickbuy', args=(1,)), {"quickbuy": "jokke 1"})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "stregsystem/index_sale.html")

        (args, kwargs) = fulfill.call_args
        (last_trans,) = args
        self.assertEqual(last_trans, PayTransaction(900))

    @patch('stregsystem.models.Member.can_fulfill')
    @patch('stregsystem.models.Member.fulfill')
    def test_make_sale_quickbuy_fail(self, fulfill, can_fulfill):
        can_fulfill.return_value = False

        response = self.client.post(reverse('quickbuy', args=(1,)), {"quickbuy": "jan 1"})

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
        (last_trans,) = args
        self.assertEqual(last_trans, PayTransaction(900))


class TransactionTests(TestCase):
    def test_pay_transaction_change_neg(self):
        transaction = PayTransaction(100)
        self.assertEqual(transaction.change(), -100)

    def test_pay_transaction_change_pos(self):
        transaction = GetTransaction(100)
        self.assertEqual(transaction.change(), 100)


class MemberTests(TestCase):
    def test_fulfill_pay_transaction(self):
        member = Member(
            balance=100
        )
        transaction = PayTransaction(10)
        member.fulfill(transaction)

        self.assertEqual(member.balance, 90)

    def test_fulfill_pay_transaction_no_money(self):
        member = Member(
            balance=2
        )
        transaction = PayTransaction(10)
        with self.assertRaises(StregForbudError) as c:
            member.fulfill(transaction)

        self.assertTrue(c.exception)
        self.assertEqual(member.balance, 2)

    def test_fulfill_check_transaction_has_money(self):
        member = Member(
            balance=10
        )
        transaction = PayTransaction(10)

        has_money = member.can_fulfill(transaction)

        self.assertTrue(has_money)

    def test_fulfill_check_transaction_no_money(self):
        member = Member(
            balance=2
        )
        transaction = PayTransaction(10)

        has_money = member.can_fulfill(transaction)

        self.assertFalse(has_money)


class AdminTests(TestCase):
    def test_product_activated_filter(self):
        Product.objects.create(name="active_dec_none", price=1.0, active=True, deactivate_date=None)
        Product.objects.create(name="active_dec_future", price=1.0, active=True, deactivate_date=datetime.datetime.now() + datetime.timedelta(hours=1))
        Product.objects.create(name="active_dec_past", price=1.0, active=True, deactivate_date=datetime.datetime.now() - datetime.timedelta(hours=1))

        Product.objects.create(name="deactivated_dec_none", price=1.0, active=False, deactivate_date=None)
        Product.objects.create(name="deactivated_dec_future", price=1.0, active=False, deactivate_date=datetime.datetime.now() + datetime.timedelta(hours=1))
        Product.objects.create(name="deactivated_dec_past", price=1.0, active=False, deactivate_date=datetime.datetime.now() - datetime.timedelta(hours=1))

        f_1 = admin.ProductActivatedListFilter(None, {'activated': 'Yes'}, Product, ProductAdmin)
        poll_1 = list(f_1.queryset(None, Product.objects.all()))

        f_2 = admin.ProductActivatedListFilter(None, {'activated': 'No'}, Product, ProductAdmin)
        poll_2 = list(f_2.queryset(None, Product.objects.all()))

        for e in ["active_dec_none", "active_dec_future"]:
            self.assertIn(Product.objects.get(name=e), poll_1)
            self.assertNotIn(Product.objects.get(name=e), poll_2)

        for e in ["active_dec_past", "deactivated_dec_none", "deactivated_dec_future", "deactivated_dec_past"]:
            self.assertIn(Product.objects.get(name=e), poll_2)
            self.assertNotIn(Product.objects.get(name=e), poll_1)



