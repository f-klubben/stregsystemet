# -*- coding: utf-8 -*-
import datetime
from collections import Counter
from unittest.mock import patch

import pytz
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.forms import model_to_dict
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

import stregsystem.parser as parser
from stregreport import views
from stregsystem import admin
from stregsystem import views as stregsystem_views
from stregsystem.admin import CategoryAdmin, MemberForm, ProductAdmin
from stregsystem.booze import ballmer_peak
from stregsystem.models import (
    Category,
    GetTransaction,
    Member,
    NoMoreInventoryError,
    Order,
    OrderItem,
    Payment,
    PayTransaction,
    Product,
    Room,
    Sale,
    StregForbudError,
    active_str,
    price_display
)


def assertCountEqual(case, *args, **kwargs):
    try:
        case.assertCountEqual(*args, **kwargs)
    except AttributeError:
        case.assertItemsEqual(*args, **kwargs)


class ModelMiscTests(TestCase):
    def test_price_display_none(self):
        v = price_display(None)
        self.assertEqual(v, "0.00 kr.")

    def test_price_display_zero(self):
        v = price_display(0)
        self.assertEqual(v, "0.00 kr.")

    def test_price_display_one(self):
        v = price_display(1)
        self.assertEqual(v, "0.01 kr.")

    def test_price_display_hundred(self):
        v = price_display(100)
        self.assertEqual(v, "1.00 kr.")

    def test_active_str_true(self):
        v = active_str(True)
        self.assertEqual(v, "+")

    def test_active_str_false(self):
        v = active_str(False)
        self.assertEqual(v, "-")


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

        assertCountEqual(self, response.context["products"], {
            Product.objects.get(id=1)
        })
        self.assertEqual(response.context["member"],
                         Member.objects.get(username="jokke"))

        fulfill.assert_called_once_with(PayTransaction(900))

    def test_make_sale_quickbuy_fail(self):
        member_username = 'jan'
        member_before = Member.objects.get(username=member_username)
        response = self.client.post(
            reverse('quickbuy', args=(1,)),
            {"quickbuy": member_username + " 1"}
        )
        member_after = Member.objects.get(username=member_username)

        self.assertEqual(response.status_code, 402)
        self.assertTemplateUsed(response, "stregsystem/error_stregforbud.html")
        self.assertEqual(member_before.balance, member_after.balance)

        self.assertEqual(response.context["member"],
                         Member.objects.get(username=member_username))

    def test_make_sale_quickbuy_wrong_product(self):
        response = self.client.post(
            reverse('quickbuy', args=(1,)),
            {"quickbuy": "jokke 99"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "stregsystem/error_productdoesntexist.html")

    @patch('stregsystem.models.Member.can_fulfill')
    def test_make_sale_menusale_fail(self, can_fulfill):
        can_fulfill.return_value = False
        member_id = 1
        member_before = Member.objects.get(id=member_id)

        response = self.client.get(reverse('menu_sale', args=(1, member_id, 1)))

        member_after = Member.objects.get(id=member_id)

        self.assertEqual(member_before.balance, member_after.balance)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "stregsystem/error_stregforbud.html")
        self.assertEqual(response.context["member"], Member.objects.get(id=1))

    @patch('stregsystem.models.Member.can_fulfill')
    @patch('stregsystem.models.Member.fulfill')
    def test_make_sale_menusale_success(self, fulfill, can_fulfill):
        can_fulfill.return_value = True

        response = self.client.get(reverse('menu_sale', args=(1, 1, 1)))
        self.assertTemplateUsed(response, "stregsystem/menu.html")

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.context["bought"], Product.objects.get(id=1))
        self.assertEqual(response.context["member"], Member.objects.get(id=1))

        fulfill.assert_called_once_with(PayTransaction(900))

    def test_quicksale_has_status_line(self):
        response = self.client.post(
            reverse('quickbuy', args=(1,)),
            {"quickbuy": "jokke 1"}
        )

        self.assertContains(
            response,
            "<b>jokke har lige købt Limfjordsporter for tilsammen "
            "9.00 kr.</b>",
            html=True
        )

    def test_usermenu(self):
        response = self.client.post(
            reverse('quickbuy', args=(1,)),
            {"quickbuy": "jokke"}
        )

        self.assertTemplateUsed(response, "stregsystem/menu.html")

    def test_quickbuy_empty(self):
        response = self.client.post(
            reverse('quickbuy', args=(1,)),
            {"quickbuy": ""}
        )

        self.assertTemplateUsed(response, "stregsystem/index.html")

    def test_index(self):
        response = self.client.post(
            reverse('index')
        )

        # Assert permanent redirect
        self.assertEqual(response.status_code, 301)

    def test_menu_index(self):
        response = self.client.post(
            reverse('menu_index', args=(1,))
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "stregsystem/index.html")
        # Assert that the index screen at least contains one of the products in
        # the database. Technically this doesn't check everything exhaustively,
        # but it's better than nothing -Jesper 18/09-2017
        self.assertContains(response, "<td>Limfjordsporter</td>", html=True)

    def test_quickbuy_no_known_member(self):
        response = self.client.post(
            reverse('quickbuy', args=(1,)),
            {"quickbuy": "notinthere"}
        )

        self.assertTemplateUsed(
            response,
            "stregsystem/error_usernotfound.html"
        )

    def test_quicksale_increases_bought(self):
        before = Product.objects.get(id=2)
        before_bought = before.bought
        before_member = Member.objects.get(username="jokke")

        response = self.client.post(
            reverse('quickbuy', args=(1,)),
            {"quickbuy": "jokke 2"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "stregsystem/index_sale.html")

        after = Product.objects.get(id=2)
        after_member = Member.objects.get(username="jokke")

        self.assertEqual(before_bought + 1, after.bought)
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

    def test_quicksale_product_not_in_room(self):
        before_product = Product.objects.get(id=4)
        before_member = Member.objects.get(username="jokke")

        response = self.client.post(
            reverse('quickbuy', args=(1,)),
            {"quickbuy": "jokke 4"}
        )

        after_product = Product.objects.get(id=4)
        after_member = Member.objects.get(username="jokke")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "stregsystem/error_productdoesntexist.html")

        self.assertEqual(before_product.bought, after_product.bought)
        self.assertEqual(before_member.balance, after_member.balance)

    def test_quicksale_product_available_all_rooms(self):
        before_member = Member.objects.get(username="jokke")

        response = self.client.post(
            reverse('quickbuy', args=(1,)),
            {"quickbuy": "jokke 1"}
        )

        after_member = Member.objects.get(username="jokke")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "stregsystem/index_sale.html")

        self.assertEqual(before_member.balance - 900, after_member.balance)

    def test_menusale_product_not_in_room(self):
        before_product = Product.objects.get(id=4)
        before_member = Member.objects.get(username="jokke")

        response = self.client.get(reverse('menu_sale', args=(1, before_member.id, 4)))

        after_product = Product.objects.get(id=4)
        after_member = Member.objects.get(username="jokke")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "stregsystem/menu.html")

        self.assertEqual(before_product.bought, after_product.bought)
        self.assertEqual(before_member.balance, after_member.balance)

    def test_multibuy_hint_not_applicable(self):
        member = Member.objects.get(username="jokke")
        give_multibuy_hint, sale_hints = stregsystem_views._multibuy_hint(timezone.now(), member)
        self.assertFalse(give_multibuy_hint)
        self.assertIsNone(sale_hints)

    def test_multibuy_hint_one_buy_not_applicable(self):
        member = Member.objects.get(username="jokke")
        coke = Product.objects.create(
            name="coke",
            price=100,
            active=True
        )
        Sale.objects.create(
            member=member,
            product=coke,
            price=100,
        )
        give_multibuy_hint, sale_hints = stregsystem_views._multibuy_hint(timezone.now(), member)
        self.assertFalse(give_multibuy_hint)
        self.assertIsNone(sale_hints)

    def test_multibuy_hint_two_buys_applicable(self):
        member = Member.objects.get(username="jokke")
        coke = Product.objects.create(
            name="coke",
            price=100,
            active=True
        )
        with freeze_time(timezone.datetime(2018, 1, 1)) as frozen_time:
            for i in range(1, 3):
                Sale.objects.create(
                    member=member,
                    product=coke,
                    price=100,
                )
                frozen_time.tick()
        give_multibuy_hint, sale_hints = stregsystem_views._multibuy_hint(
            timezone.datetime(2018, 1, 1, tzinfo=pytz.UTC), member)
        self.assertTrue(give_multibuy_hint)
        self.assertEqual(sale_hints, "{} {}:{}".format("jokke", coke.id, 2))


class UserInfoViewTests(TestCase):
    def setUp(self):
        self.room = Room.objects.create(
            name="test"
        )
        self.jokke = Member.objects.create(
            username="jokke"
        )
        self.coke = Product.objects.create(
            name="coke",
            price=100,
            active=True
        )
        self.flan = Product.objects.create(
            name="flan",
            price=200,
            active=True
        )
        self.sales = []
        with freeze_time(timezone.datetime(2000, 1, 1)) as frozen_time:
            for i in range(1, 4):
                self.sales.append(
                    Sale.objects.create(
                        member=self.jokke,
                        product=self.coke,
                        price=100,
                    )
                )
                frozen_time.tick()
        self.payments = []
        with freeze_time(timezone.datetime(2000, 1, 1)) as frozen_time:
            for i in range(1, 3):
                self.payments.append(
                    Payment.objects.create(
                        member=self.jokke,
                        amount=100,
                    )
                )
                frozen_time.tick()

    def test_renders(self):
        response = self.client.post(
            reverse('userinfo', args=(self.room.id, self.jokke.id)),
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "stregsystem/menu_userinfo.html")

    def test_last_sale(self):
        response = self.client.post(
            reverse('userinfo', args=(self.room.id, self.jokke.id)),
        )

        self.assertSequenceEqual(
            response.context["last_sale_list"],
            self.sales[::-1]
        )

    def test_last_payment(self):
        response = self.client.post(
            reverse('userinfo', args=(self.room.id, self.jokke.id)),
        )

        self.assertEqual(
            response.context["last_payment"],
            self.payments[-1]
        )

    # @INCOMPLETE: Strictly speaking there are two more variables here. Are
    # they actually necessary, since we don't allow people to go negative
    # anymore anyway? - Jesper 18/09-2017


class TransactionTests(TestCase):
    def test_pay_transaction_change_neg(self):
        transaction = PayTransaction(100)
        self.assertEqual(transaction.change(), -100)

    def test_pay_transaction_add(self):
        transaction = PayTransaction(90)
        transaction.add(10)
        self.assertEqual(transaction.change(), -100)

    def test_get_transaction_change_pos(self):
        transaction = GetTransaction(100)
        self.assertEqual(transaction.change(), 100)

    def test_get_transaction_change_add(self):
        transaction = GetTransaction(90)
        transaction.add(10)
        self.assertEqual(transaction.change(), 100)


class OrderTest(TestCase):
    def setUp(self):
        self.member = Member.objects.create(balance=100)
        self.room = Room.objects.create(name="room")
        self.product = Product.objects.create(
            id=1,
            name="øl",
            price=10,
            active=True,
        )

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
        self.product.sale_set.create(
            price=100,
            member=self.member
        )
        self.product.start_date = datetime.date(year=2017, month=1, day=1)
        self.product.quantity = 1
        order = Order(self.member, self.room)

        item = OrderItem(self.product, order, 1)
        order.items.add(item)

        with self.assertRaises(NoMoreInventoryError):
            order.execute()

        fulfill.was_not_called()

    @patch('stregsystem.models.Member.fulfill')
    def test_order_execute_multi_some_remaining(self, fulfill):
        self.product.sale_set.create(
            price=100,
            member=self.member
        )
        self.product.start_date = datetime.date(year=2017, month=1, day=1)
        self.product.quantity = 2
        order = Order(self.member, self.room)

        item = OrderItem(self.product, order, 2)
        order.items.add(item)

        with self.assertRaises(NoMoreInventoryError):
            order.execute()

        fulfill.was_not_called()

    @patch('stregsystem.models.Member.can_fulfill')
    def test_order_execute_no_money(self, can_fulfill):
        can_fulfill.return_value = False
        balance_before = self.member.balance
        order = Order(self.member, self.room)

        item = OrderItem(self.product, order, 2)
        order.items.add(item)

        with self.assertRaises(StregForbudError):
            order.execute()

        balance_after = self.member.balance
        self.assertEqual(balance_before, balance_after)


class PaymentTests(TestCase):
    def setUp(self):
        self.member = Member.objects.create(
            username="jon",
            balance=100
        )

    @patch("stregsystem.models.Member.make_payment")
    def test_payment_save_not_saved(self, make_payment):
        payment = Payment(
            member=self.member,
            amount=100
        )

        payment.save()

        make_payment.assert_called_once_with(100)

    @patch("stregsystem.models.Member.make_payment")
    def test_payment_save_already_saved(self, make_payment):
        payment = Payment(
            member=self.member,
            amount=100
        )
        payment.save()
        make_payment.reset_mock()

        payment.save()

        make_payment.assert_not_called()

    @patch("stregsystem.models.Member.make_payment")
    def test_payment_delete_already_saved(self, make_payment):
        payment = Payment(
            member=self.member,
            amount=100
        )
        payment.save()
        make_payment.reset_mock()

        payment.delete()

        make_payment.assert_called_once_with(-100)

    @patch("stregsystem.models.Member.make_payment")
    def test_payment_delete_not_saved(self, make_payment):
        payment = Payment(
            member=self.member,
            amount=100
        )

        with self.assertRaises(AssertionError):
            payment.delete()


class ProductTests(TestCase):
    def setUp(self):
        self.jeff = Member.objects.create(
            username="Jeff",
        )

    def test_is_active_active(self):
        product = Product.objects.create(
            active=True,
            price=100,
        )

        self.assertTrue(product.is_active())

    def test_is_active_active_not_expired(self):
        product = Product.objects.create(
            active=True,
            price=100,
            deactivate_date=(timezone.now() + datetime.timedelta(hours=1))
        )

        self.assertTrue(product.is_active())

    def test_is_active_active_expired(self):
        product = Product.objects.create(
            active=True,
            price=100,
            deactivate_date=(timezone.now() - datetime.timedelta(hours=1))
        )

        self.assertFalse(product.is_active())

    def test_is_active_active_out_of_stock(self):
        product = Product.objects.create(
            active=True,
            price=100,
            quantity=1,
            start_date=datetime.date(year=2017, month=1, day=1)
        )
        product.sale_set.create(
            price=100,
            member=self.jeff
        )

        self.assertFalse(product.is_active())

    def test_is_active_active_in_stock(self):
        product = Product.objects.create(
            active=True,
            price=100,
            quantity=2,
            start_date=datetime.date(year=2017, month=1, day=1)
        )
        product.sale_set.create(
            price=100,
            member=self.jeff
        )

        self.assertTrue(product.is_active())

    def test_is_active_deactive(self):
        product = Product.objects.create(
            active=False,
            price=100,
        )

        self.assertFalse(product.is_active())

    def test_is_active_deactive_expired(self):
        product = Product.objects.create(
            active=False,
            price=100,
            deactivate_date=(timezone.now() - datetime.timedelta(hours=1))
        )

        self.assertFalse(product.is_active())

    def test_is_active_deactive_out_of_stock(self):
        product = Product.objects.create(
            active=False,
            price=100,
            quantity=1,
            start_date=datetime.date(year=2017, month=12, day=1)
        )
        product.sale_set.create(
            price=100,
            member=self.jeff
        )

        self.assertFalse(product.is_active())

    def test_is_active_deactive_in_stock(self):
        product = Product.objects.create(
            active=False,
            price=100,
            quantity=2,
            start_date=datetime.date(year=2017, month=12, day=1)
        )
        product.sale_set.create(
            price=100,
            member=self.jeff
        )

        self.assertFalse(product.is_active())