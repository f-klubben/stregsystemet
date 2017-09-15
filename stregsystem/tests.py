# -*- coding: utf8 -*-
import datetime

from django.test import TestCase
from django.urls import reverse
from collections import Counter

from stregsystem import admin
from stregsystem.utils import QuickbuyParser, QuickBuyError
from stregsystem.admin import ProductAdmin
from stregsystem.models import (
    GetTransaction,
    Member,
    PayTransaction,
    StregForbudError,
    Product,
    Room,
    Order,
    OrderItem,
    NoMoreInventoryError
)

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch


class SaleViewTests(TestCase):
    fixtures = ["initial_data"]

    def test_make_sale_letter_quickbuy(self):
        response = self.client.post(
            reverse('quickbuy', args="1"),
            {"quickbuy": "jokke a"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("stregsystem/error_invalidquickbuy.html")

    @patch('stregsystem.models.Member.can_fulfill')
    @patch('stregsystem.models.Member.fulfill')
    def test_make_sale_quickbuy_success(self, fulfill, can_fulfill):
        can_fulfill.return_value = True

        response = self.client.post(
            reverse('quickbuy', args=(1,)),
            {"quickbuy": "jokke 1"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "stregsystem/index_sale.html")

        fulfill.assert_called_once_with(PayTransaction(900))

    def test_make_sale_quickbuy_fail(self):
        member_username = 'jan'
        member_before = Member.objects.get(username=member_username)
        response = self.client.post(
            reverse('quickbuy', args=(1,)),
            {"quickbuy": member_username + " 1"}
        )
        member_after = Member.objects.get(username=member_username)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "stregsystem/error_stregforbud.html")
        self.assertEqual(member_before.balance, member_after.balance)

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

        fulfill.assert_called_once_with(PayTransaction(900))

    def test_quicksale_has_status_line(self):
        response = self.client.post(
            reverse('quickbuy', args=(1,)),
            {"quickbuy": "jokke 1"}
        )

        self.assertContains(response, "<b>jokke har lige købt Limfjordsporter for tilsammen 9.00 kr.</b>", html=True)

    def test_usermenu(self):
        response = self.client.post(
            reverse('quickbuy', args=(1,)),
            {"quickbuy": "jokke"}
        )

        self.assertTemplateUsed(response, "stregsystem/menu.html")

    def test_index(self):
        response = self.client.post(
            reverse('quickbuy', args=(1,)),
            {"quickbuy": ""}
        )

        self.assertTemplateUsed(response, "stregsystem/index.html")

    def test_quicksale_increases_bought(self):
        before = Product.objects.get(id=2)
        before_member = Member.objects.get(username="jokke")

        response = self.client.post(
            reverse('quickbuy', args=(1,)),
            {"quickbuy": "jokke 2"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "stregsystem/index_sale.html")

        after = Product.objects.get(id=2)
        after_member = Member.objects.get(username="jokke")

        self.assertEqual(before.bought + 1, after.bought)
        # 900 is the product price
        self.assertEqual(before_member.balance - 900, after_member.balance)

    def test_quicksale_quanitity_none_noincrease(self):
        before = Product.objects.get(id=1)
        before_member = Member.objects.get(username="jokke")

        response = self.client.post(
            reverse('quickbuy', args=(1,)),
            {"quickbuy": "jokke 1"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "stregsystem/index_sale.html")

        after = Product.objects.get(id=1)
        after_member = Member.objects.get(username="jokke")

        self.assertEqual(before.bought, after.bought)
        # 900 is the product price
        self.assertEqual(before_member.balance - 900, after_member.balance)

    def test_quicksale_out_of_stock(self):
        before = Product.objects.get(id=1)
        before_member = Member.objects.get(username="jokke")

        response = self.client.post(
            reverse('quickbuy', args=(1,)),
            {"quickbuy": "jokke 3"}
        )

        self.assertEqual(response.status_code, 200)
        # I don't know which template to use (I should probably make one). So
        # for now let's just make sure that we at least don't use the one that
        # says "correct" - Jesper 14/09-2017
        self.assertTemplateNotUsed(response, "stregsystem/index_sale.html")

        after = Product.objects.get(id=1)
        after_member = Member.objects.get(username="jokke")

        self.assertEqual(before.bought, after.bought)
        self.assertEqual(before_member.balance, after_member.balance)


class TransactionTests(TestCase):
    def test_pay_transaction_change_neg(self):
        transaction = PayTransaction(100)
        self.assertEqual(transaction.change(), -100)

    def test_pay_transaction_change_pos(self):
        transaction = GetTransaction(100)
        self.assertEqual(transaction.change(), 100)


class OrderTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(balance=100)
        self.room = Room.objects.create(name="room")
        self.product = Product.objects.create(id=1, name="øl", price=10,
                                              active=True)

    def test_order_fromproducts(self):
        products = [
            self.product,
            self.product,
        ]
        order = Order.from_products(self.member, self.room, products)
        self.assertEqual(
            list(Counter(products).items()),
            [(item.product, item.count) for item in order.items]
        )

    def test_order_total_single_item(self):
        order = Order(self.member, self.room)

        item = OrderItem(self.product, order, 1)
        order.items.add(item)

        self.assertEqual(order.total(), 10)

    def test_order_total_multi_item(self):
        order = Order(self.member, self.room)

        item = OrderItem(self.product, order, 2)
        order.items.add(item)

        self.assertEqual(order.total(), 20)

    @patch('stregsystem.models.Member.fulfill')
    def test_order_execute_single_transaction(self, fulfill):
        order = Order(self.member, self.room)

        item = OrderItem(self.product, order, 1)
        order.items.add(item)

        order.execute()

        fulfill.assert_called_once_with(PayTransaction(10))

    @patch('stregsystem.models.Member.fulfill')
    def test_order_execute_multi_transaction(self, fulfill):
        order = Order(self.member, self.room)

        item = OrderItem(self.product, order, 2)
        order.items.add(item)

        order.execute()

        fulfill.assert_called_once_with(PayTransaction(20))

    @patch('stregsystem.models.Member.fulfill')
    def test_order_execute_single_no_remaining(self, fulfill):
        self.product.bought = 1
        self.product.quantity = 1
        order = Order(self.member, self.room)

        item = OrderItem(self.product, order, 1)
        order.items.add(item)

        with self.assertRaises(NoMoreInventoryError):
            order.execute()

        fulfill.was_not_called()

    @patch('stregsystem.models.Member.fulfill')
    def test_order_execute_multi_some_remaining(self, fulfill):
        self.product.bought = 1
        self.product.quantity = 2
        order = Order(self.member, self.room)

        item = OrderItem(self.product, order, 2)
        order.items.add(item)

        with self.assertRaises(NoMoreInventoryError):
            order.execute()

        fulfill.was_not_called()

    @patch('stregsystem.models.Member.can_fulfill')
    @patch('stregsystem.models.Member.fulfill')
    def test_order_execute_no_money(self, fulfill, can_fulfill):
        can_fulfill.return_value = False
        order = Order(self.member, self.room)

        item = OrderItem(self.product, order, 2)
        order.items.add(item)

        with self.assertRaises(StregForbudError):
            order.execute()

        fulfill.was_not_called()


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


class ProductActivatedListFilterTests(TestCase):
    def setUp(self):
        Product.objects.create(
            name="active_dec_none",
            price=1.0, active=True,
            deactivate_date=None
        )
        Product.objects.create(
            name="active_dec_future",
            price=1.0,
            active=True,
            deactivate_date=(datetime.datetime.now()
                             + datetime.timedelta(hours=1))
        )
        Product.objects.create(
            name="active_dec_past",
            price=1.0,
            active=True,
            deactivate_date=(datetime.datetime.now()
                             - datetime.timedelta(hours=1))
        )

        Product.objects.create(
            name="deactivated_dec_none",
            price=1.0,
            active=False,
            deactivate_date=None
        )
        Product.objects.create(
            name="deactivated_dec_future",
            price=1.0,
            active=False,
            deactivate_date=(datetime.datetime.now()
                             + datetime.timedelta(hours=1))
        )
        Product.objects.create(
            name="deactivated_dec_past",
            price=1.0,
            active=False,
            deactivate_date=(datetime.datetime.now()
                             - datetime.timedelta(hours=1))
        )
        Product.objects.create(
            name="active_none_left",
            price=1.0,
            active=True,
            bought=2,
            quantity=2,
        )
        Product.objects.create(
            name="active_some_left",
            price=1.0,
            active=True,
            bought=0,
            quantity=2,
        )

    def test_active_trivial(self):
        fy = admin.ProductActivatedListFilter(
            None,
            {'activated': 'Yes'},
            Product,
            ProductAdmin
        )
        qy = list(fy.queryset(None, Product.objects.all()))
        fn = admin.ProductActivatedListFilter(
            None,
            {'activated': 'No'},
            Product,
            ProductAdmin
        )
        qn = list(fn.queryset(None, Product.objects.all()))

        self.assertIn(Product.objects.get(name="active_dec_none"), qy)
        self.assertNotIn(Product.objects.get(name="active_dec_none"), qn)

    def test_active_deac_future(self):
        fy = admin.ProductActivatedListFilter(
            None,
            {'activated': 'Yes'},
            Product,
            ProductAdmin
        )
        qy = list(fy.queryset(None, Product.objects.all()))
        fn = admin.ProductActivatedListFilter(
            None,
            {'activated': 'No'},
            Product,
            ProductAdmin
        )
        qn = list(fn.queryset(None, Product.objects.all()))

        self.assertIn(Product.objects.get(name="active_dec_future"), qy)
        self.assertNotIn(Product.objects.get(name="active_dec_future"), qn)

    def test_active_deac_past(self):
        fy = admin.ProductActivatedListFilter(
            None,
            {'activated': 'Yes'},
            Product,
            ProductAdmin
        )
        qy = list(fy.queryset(None, Product.objects.all()))
        fn = admin.ProductActivatedListFilter(
            None,
            {'activated': 'No'},
            Product,
            ProductAdmin
        )
        qn = list(fn.queryset(None, Product.objects.all()))

        self.assertNotIn(Product.objects.get(name="active_dec_past"), qy)
        self.assertIn(Product.objects.get(name="active_dec_past"), qn)

    def test_inactive_trivial(self):
        fy = admin.ProductActivatedListFilter(
            None,
            {'activated': 'Yes'},
            Product,
            ProductAdmin
        )
        qy = list(fy.queryset(None, Product.objects.all()))
        fn = admin.ProductActivatedListFilter(
            None,
            {'activated': 'No'},
            Product,
            ProductAdmin
        )
        qn = list(fn.queryset(None, Product.objects.all()))

        self.assertNotIn(Product.objects.get(name="deactivated_dec_none"), qy)
        self.assertIn(Product.objects.get(name="deactivated_dec_none"), qn)

    def test_inactive_deac_future(self):
        fy = admin.ProductActivatedListFilter(
            None,
            {'activated': 'Yes'},
            Product,
            ProductAdmin
        )
        qy = list(fy.queryset(None, Product.objects.all()))
        fn = admin.ProductActivatedListFilter(
            None,
            {'activated': 'No'},
            Product,
            ProductAdmin
        )
        qn = list(fn.queryset(None, Product.objects.all()))

        self.assertNotIn(
            Product.objects.get(name="deactivated_dec_future"),
            qy
        )
        self.assertIn(Product.objects.get(name="deactivated_dec_future"), qn)

    def test_inactive_deac_past(self):
        fy = admin.ProductActivatedListFilter(
            None,
            {'activated': 'Yes'},
            Product,
            ProductAdmin
        )
        qy = list(fy.queryset(None, Product.objects.all()))
        fn = admin.ProductActivatedListFilter(
            None,
            {'activated': 'No'},
            Product,
            ProductAdmin
        )
        qn = list(fn.queryset(None, Product.objects.all()))

        self.assertNotIn(Product.objects.get(name="deactivated_dec_past"), qy)
        self.assertIn(Product.objects.get(name="deactivated_dec_past"), qn)

    def test_active_none_left(self):
        fy = admin.ProductActivatedListFilter(
            None,
            {'activated': 'Yes'},
            Product,
            ProductAdmin
        )
        qy = list(fy.queryset(None, Product.objects.all()))
        fn = admin.ProductActivatedListFilter(
            None,
            {'activated': 'No'},
            Product,
            ProductAdmin
        )
        qn = list(fn.queryset(None, Product.objects.all()))

        self.assertNotIn(Product.objects.get(name="active_none_left"), qy)
        self.assertIn(Product.objects.get(name="active_none_left"), qn)

    def test_active_some_left(self):
        fy = admin.ProductActivatedListFilter(
            None,
            {'activated': 'Yes'},
            Product,
            ProductAdmin
        )
        qy = list(fy.queryset(None, Product.objects.all()))
        fn = admin.ProductActivatedListFilter(
            None,
            {'activated': 'No'},
            Product,
            ProductAdmin
        )
        qn = list(fn.queryset(None, Product.objects.all()))

        self.assertIn(Product.objects.get(name="active_some_left"), qy)
        self.assertNotIn(Product.objects.get(name="active_some_left"), qn)


class QuickbuyParserTests(TestCase):
    def setUp(self):
        self.test_username = 'test'
        try:
            self.assertCountEqual = self.assertCountEqual
        except AttributeError:
            self.assertCountEqual = self.assertItemsEqual

    def test_username_only(self):
        buy_string = self.test_username

        username, products = QuickbuyParser.parse(buy_string)

        self.assertEqual(self.test_username, username)
        self.assertEqual(len(products), 0)

    def test_single_buy(self):
        product_ids = [42]
        buy_string = self.test_username + ' 42'

        username, products = QuickbuyParser.parse(buy_string)

        self.assertEqual(username, self.test_username)
        self.assertEqual(len(products), 1)
        self.assertCountEqual(product_ids, products)

    def test_multi_buy(self):
        product_ids = [42, 1337]
        buy_string = self.test_username + " 42 1337"

        username, products = QuickbuyParser.parse(buy_string)

        self.assertEqual(username, self.test_username)
        self.assertEqual(len(products), len(product_ids))
        self.assertCountEqual(product_ids, products)

    def test_multi_buy_repeated(self):
        product_ids = [42, 42]
        buy_string = self.test_username + " 42 42"

        username, products = QuickbuyParser.parse(buy_string)

        self.assertEqual(username, self.test_username)
        self.assertEqual(len(products), len(product_ids))
        self.assertCountEqual(product_ids, products)

    def test_multi_buy_quantifier(self):
        product_ids = [42, 42, 1337, 1337, 1337]
        buy_string = self.test_username + " 42:2 1337:3"

        username, products = QuickbuyParser.parse(buy_string)

        self.assertEqual(username, self.test_username)
        self.assertEqual(len(products), len(product_ids))
        self.assertCountEqual(product_ids, products)

    def test_zero_quantifier(self):
        buy_string = self.test_username + " 42:0"

        username, products = QuickbuyParser.parse(buy_string)

        self.assertEqual(username, self.test_username)
        self.assertEqual(len(products), 0)

    def test_negative_quantifier(self):
        buy_string = self.test_username + ' 42:-1 1337:3'
        with self.assertRaises(QuickBuyError):
            QuickbuyParser.parse(buy_string)

    def test_missing_quantifier(self):
        buy_string = self.test_username + ' 42: 1337:3'
        with self.assertRaises(QuickBuyError):
            QuickbuyParser.parse(buy_string)

    def test_invalid_quantifier(self):
        buy_string = self.test_username + ' 42:a 1337:3'
        with self.assertRaises(QuickBuyError):
            QuickbuyParser.parse(buy_string)

    def test_invalid_productId(self):
        buy_string = self.test_username + ' a:2 1337:3'
        with self.assertRaises(QuickBuyError):
            QuickbuyParser.parse(buy_string)
