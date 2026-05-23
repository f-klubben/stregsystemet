import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from events.models import TicketRecord, Event, EventInstance, Ticket
from stregsystem.models import (
    InvalidTicketRecordError,
    InvalidTicketError,
    Member,
    Product,
    Sale,
)


# Create your tests here.
class EventAndTicketTests(TestCase):
    """
    setUpClass()
    setUpTestData()

    For each test method:
        Start transaction
        setUp()
        test_*
        tearDown()
        Rollback transaction

    tearDownClass()
    """

    fixtures = ["initial_data"]

    def helper_create_ticket_record(
        self, member: Member, product: Product, is_standby=False
    ) -> tuple[TicketRecord, Sale]:
        # Helper method to create a ticket record, since the sale implicitly does this, and this is done many times.
        sale = Sale.objects.create(member=member, product=product, price=product.price)
        ticket_record = TicketRecord.objects.filter(sale=sale).first()
        if ticket_record is None:
            self.fail("TicketRecord was not created for the sale.")
        ticket_record.is_stand_by = is_standby
        ticket_record.save()
        return ticket_record, sale

    def helper_emulate_sale(self, product_id: int):
        response = self.client.post(
            reverse("quickbuy", args=(1,)),
            {"quickbuy": f"test {product_id}"},
        )

        self.assertEqual(response.status_code, 200)

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        cls.member = Member.objects.create(username="test", email="test@example.com", balance=10000)

        cls.member_2 = Member.objects.create(username="test2", email="test2@example.com", balance=10000)

        cls.admin = User.objects.create_superuser('admin', 'admin@example.com', 'adminpassword')

        cls.event = Event.objects.create(name="Test Event", description="This is a test event.")

        cls.event_instance = EventInstance.objects.create(
            event=cls.event,
            name_overwrite="Test Event Instance",
            description_overwrite="This is a test event instance.",
            capacity=5,
            start_time=timezone.now(),
            end_time=timezone.now() + datetime.timedelta(hours=2),
            final_refund_time=timezone.now() + datetime.timedelta(hours=10),
            location="Test Location",
        )

        cls.event_instance_2 = EventInstance.objects.create(
            event=cls.event,
            capacity=5,
            start_time=timezone.now() + datetime.timedelta(hours=3),
            end_time=timezone.now() + datetime.timedelta(hours=6),
            final_refund_time=timezone.now() + datetime.timedelta(hours=10),
            location="Test Location 2",
        )

        cls.event_instance_low_capacity = EventInstance.objects.create(
            event=cls.event,
            capacity=1,
            start_time=timezone.now() + datetime.timedelta(hours=3),
            end_time=timezone.now() + datetime.timedelta(hours=6),
            final_refund_time=timezone.now() + datetime.timedelta(hours=10),
            location="Test Location 2",
        )

        cls.low_capcity_ticket = Ticket.objects.create(
            event_instance=cls.event_instance_low_capacity,
            quantity=2,
            product=Product.objects.create(name="Low Capacity Product", price=100, active=True),
        )

        cls.event_instance_not_refundable_by_user = EventInstance.objects.create(
            event=cls.event,
            name_overwrite="Test Event Instance Not Refundable By User",
            description_overwrite="This is a test event instance that is not refundable by user.",
            capacity=5,
            start_time=timezone.now() + datetime.timedelta(hours=3),
            end_time=timezone.now() + datetime.timedelta(hours=6),
            final_refund_time=timezone.now(),
            location="Test Location 3",
        )

        cls.event_instance_product = Product.objects.create(name="Test Event Instance Product", price=100, active=True)

        cls.event_instance_ticket = Ticket.objects.create(
            event_instance=cls.event_instance, quantity=1, product=cls.event_instance_product
        )

        cls.event_instance_product_2 = Product.objects.create(
            name="Test Event Instance Product 2", price=150, active=True
        )

        cls.event_instance_ticket_2 = Ticket.objects.create(
            event_instance=cls.event_instance, quantity=9, product=cls.event_instance_product_2
        )

        cls.event_instance_not_refundable_by_user_product = Product.objects.create(
            name="Test Event Instance Not Refundable By User Product", price=200, active=True
        )

        cls.event_instance_not_refundable_by_user_ticket = Ticket.objects.create(
            event_instance=cls.event_instance_not_refundable_by_user,
            quantity=5,
            product=cls.event_instance_not_refundable_by_user_product,
        )

    def test_setup(self):
        self.assertEqual(self.member.username, "test")
        self.assertEqual(self.admin.username, "admin")
        self.assertEqual(self.event.name, "Test Event")
        self.assertEqual(self.event_instance.name_overwrite, "Test Event Instance")
        self.assertEqual(self.event_instance_product.name, "Test Event Instance Product")
        self.assertEqual(self.event_instance_product_2.name, "Test Event Instance Product 2")

    def test_tr_ticket_purchase(self):
        # Purchase the product for the first ticket
        self.helper_emulate_sale(self.event_instance_ticket.product.pk)

        self.assertTrue(Sale.objects.filter(member=self.member, product=self.event_instance_ticket.product).exists())

        ticket_records = TicketRecord.objects.filter(ticket=self.event_instance_ticket)
        self.assertTrue(ticket_records.exists())
        self.assertEqual(ticket_records.count(), 1)

        ticket_record = ticket_records.first()
        self.assertIsNotNone(ticket_record)

        assert ticket_record is not None
        self.assertIsNotNone(ticket_record.ticket)
        self.assertIsNotNone(ticket_record.sale)
        self.assertIsNone(ticket_record.has_attended)
        self.assertFalse(ticket_record.is_stand_by)
        self.assertIsNone(ticket_record.admin_issued_by)
        self.assertIsNone(ticket_record.admin_issued_to)

        member_purchases = TicketRecord.get_member_purchases(self.member)

        self.assertEqual(member_purchases.count(), 1)
        member_purchase = member_purchases.first()
        self.assertIsNotNone(member_purchase)
        assert member_purchase is not None
        self.assertEqual(member_purchase.pk, ticket_record.pk)

    def test_tr_ticket_purchase_standby(self):
        # Purchase the product for the first ticket
        self.helper_emulate_sale(self.event_instance_ticket.product.pk)

        self.assertEqual(
            Sale.objects.filter(member=self.member, product=self.event_instance_ticket.product).count(),
            1,
        )

        # Purchase the product for the first ticket the second time, which should put the ticket on standby, since quantity is

        self.helper_emulate_sale(self.event_instance_ticket.product.pk)

        self.assertEqual(
            Sale.objects.filter(member=self.member, product=self.event_instance_ticket.product).count(),
            2,
        )

        ticket_records = TicketRecord.objects.filter(ticket=self.event_instance_ticket)
        self.assertTrue(ticket_records.exists())
        self.assertEqual(ticket_records.count(), 2)

        ticket_record_first = ticket_records.first()
        self.assertIsNotNone(ticket_record_first)

        assert ticket_record_first is not None
        self.assertIsNotNone(ticket_record_first.ticket)
        self.assertIsNotNone(ticket_record_first.sale)
        self.assertIsNone(ticket_record_first.has_attended)
        self.assertFalse(ticket_record_first.is_stand_by)
        self.assertIsNone(ticket_record_first.admin_issued_by)
        self.assertIsNone(ticket_record_first.admin_issued_to)

        ticket_record_last = ticket_records.last()
        self.assertIsNotNone(ticket_record_last)
        assert ticket_record_last is not None

        self.assertNotEqual(ticket_record_first.pk, ticket_record_last.pk)
        self.assertIsNotNone(ticket_record_last.ticket)
        self.assertIsNotNone(ticket_record_last.sale)
        self.assertIsNone(ticket_record_last.has_attended)
        self.assertTrue(ticket_record_last.is_stand_by)
        self.assertIsNone(ticket_record_last.admin_issued_by)
        self.assertIsNone(ticket_record_last.admin_issued_to)

        # Purchase the product for the second ticket, which should not be on standby, since quantity is 9, and only 2 has been sold so far
        self.helper_emulate_sale(self.event_instance_ticket_2.product.pk)

        self.assertEqual(
            Sale.objects.filter(member=self.member, product=self.event_instance_ticket_2.product).count(),
            1,
        )
        self.assertEqual(
            Sale.objects.filter(member=self.member).count(),
            3,
        )

        ticket_records = TicketRecord.objects.filter(ticket=self.event_instance_ticket_2)

        self.assertTrue(ticket_records.exists())
        self.assertEqual(ticket_records.count(), 1)
        ticket_record = ticket_records.first()
        self.assertIsNotNone(ticket_record)
        assert ticket_record is not None
        self.assertIsNotNone(ticket_record.ticket)
        self.assertIsNotNone(ticket_record.sale)
        self.assertIsNone(ticket_record.has_attended)
        self.assertFalse(ticket_record.is_stand_by)
        self.assertIsNone(ticket_record.admin_issued_by)
        self.assertIsNone(ticket_record.admin_issued_to)

    def test_tr_capacity_stand_by(self):
        # Purchase the product for the first ticket 5 times, which should fill the capacity and put the rest on standby, since quantity is 1, and capacity is 5
        capacity = self.event_instance.capacity

        for i in range(capacity + 1):
            self.helper_emulate_sale(self.event_instance_ticket_2.product.pk)

            self.assertEqual(
                Sale.objects.filter(member=self.member, product=self.event_instance_ticket_2.product).count(),
                i + 1,
            )

        ticket_records = TicketRecord.objects.filter(ticket=self.event_instance_ticket_2)
        self.assertTrue(ticket_records.exists())
        self.assertEqual(ticket_records.count(), capacity + 1)

        last = ticket_records.last()
        self.assertIsNotNone(last)
        assert last is not None

        # A new ticket when purchased should have:
        # Ticket and Sale linked. Attendance should not be marked by the system and is unused for now. When ticket capcity is reached, the ticket should be marked as standby. Admin issued by and to should be None, since this is not an admin issued ticket.
        for ticket_record in ticket_records:
            self.assertIsNotNone(ticket_record)
            assert ticket_record is not None
            self.assertIsNotNone(ticket_record.ticket)
            self.assertIsNotNone(ticket_record.sale)
            self.assertIsNone(ticket_record.has_attended)
            if ticket_record.pk == last.pk:
                self.assertTrue(ticket_record.is_stand_by)
            else:
                self.assertFalse(ticket_record.is_stand_by)
            self.assertIsNone(ticket_record.admin_issued_by)
            self.assertIsNone(ticket_record.admin_issued_to)

    def test_tr_throws_exception_if_admin_issued_and_sale_is_connected(self):
        # Create a ticket record with both sale and admin issued, which should throw an exception, since this is not a valid state for a ticket record
        with self.assertRaises(InvalidTicketRecordError):
            ticket_record, _ = self.helper_create_ticket_record(self.member, self.event_instance_ticket.product)
            ticket_record.admin_issued_by = self.admin
            ticket_record.admin_issued_to = self.member
            ticket_record.save()

        # Save a ticket record which is stand by and the sale is refunded, which should throw an exception, since this is not a valid state for a ticket record
        with self.assertRaises(InvalidTicketRecordError):
            ticket_record, sale = self.helper_create_ticket_record(self.member, self.event_instance_ticket.product)
            sale.process_refund(None)

            ticket_record.refresh_from_db()
            ticket_record.is_stand_by = True
            ticket_record.save()

        # Check that it is not thrown given either one or the other, since both are valid states for a ticket record
        try:
            ticket_record, _ = self.helper_create_ticket_record(self.member, self.event_instance_ticket.product)
        except InvalidTicketRecordError:
            self.fail(
                "InvalidTicketRecordError was raised when creating a TicketRecord with a sale and no admin issue, which is a valid state for a TicketRecord."
            )

        try:
            TicketRecord.objects.create(
                ticket=self.event_instance_ticket,
                sale=None,
                is_stand_by=False,
                admin_issued_by=self.admin,
                admin_issued_to=self.member,
            )
        except InvalidTicketRecordError:
            self.fail(
                "InvalidTicketRecordError was raised when creating a TicketRecord with no sale and an admin issue, which is a valid state for a TicketRecord."
            )

    def test_tr_get_ticket_owner(self):
        # Create a ticket record with a sale, and check that the owner is returned correctly
        ticket_record, _ = self.helper_create_ticket_record(self.member, self.event_instance_ticket.product)

        ticket_owner = ticket_record.get_ticket_owner()
        self.assertIsNotNone(ticket_owner)
        assert ticket_owner is not None

        self.assertEqual(ticket_owner, self.member)

        # Create a ticket record with an admin issue, and check that the owner is returned correctly
        ticket_record_admin = TicketRecord.objects.create(
            ticket=self.event_instance_ticket,
            sale=None,
            is_stand_by=False,
            admin_issued_by=self.admin,
            admin_issued_to=self.member,
        )

        ticket_owner_admin = ticket_record_admin.get_ticket_owner()

        self.assertIsNotNone(ticket_owner_admin)
        assert ticket_owner_admin is not None

        self.assertEqual(ticket_owner_admin, self.member)

    def test_tr_get_stand_by_pretty(self):
        # Create a ticket record that is stand by
        ticket_record = TicketRecord.objects.create(
            ticket=self.event_instance_ticket,
            sale=None,
            is_stand_by=True,
            admin_issued_by=self.admin,
            admin_issued_to=self.member,
        )

        self.assertEqual(ticket_record.get_stand_by_pretty(), "Ja")

        # Create a ticket record that is not stand by
        ticket_record = TicketRecord.objects.create(
            ticket=self.event_instance_ticket,
            sale=None,
            is_stand_by=False,
            admin_issued_by=self.admin,
            admin_issued_to=self.member,
        )

        self.assertEqual(ticket_record.get_stand_by_pretty(), "Nej")

    def test_tr_get_refunded_pretty_and_is_refunded(self):
        ticket_record, sale = self.helper_create_ticket_record(self.member, self.event_instance_ticket.product)

        self.assertFalse(ticket_record.is_refunded())
        self.assertEqual(ticket_record.get_refunded_pretty(), "Nej")

        sale.process_refund(None)

        ticket_record.refresh_from_db()
        self.assertTrue(ticket_record.is_refunded())
        self.assertEqual(ticket_record.get_refunded_pretty(), "Ja")

    def test_tr_is_refundable_by_both(self):
        ticket_record, _ = self.helper_create_ticket_record(self.member, self.event_instance_ticket.product)

        self.assertTrue(ticket_record.is_refundable_by_self())
        self.assertTrue(ticket_record.is_refundable_by_admin())

        # Mark sale as refunded, which should make the ticket record not refundable
        assert ticket_record.sale is not None
        ticket_record.sale.refunded_at = timezone.now()

        self.assertFalse(ticket_record.is_refundable_by_self())
        self.assertFalse(ticket_record.is_refundable_by_admin())

        # Create a ticket record that is admin issued, which should not be refundable, since it is not connected to a sale
        ticket_record_admin = TicketRecord.objects.create(
            ticket=self.event_instance_ticket,
            sale=None,
            is_stand_by=False,
            admin_issued_by=self.admin,
            admin_issued_to=self.member,
        )

        self.assertFalse(ticket_record_admin.is_refundable_by_self())
        self.assertFalse(ticket_record_admin.is_refundable_by_admin())

    def test_tr_process_refund(self):
        # Create a ticket record that is stand by
        ticket_record, _ = self.helper_create_ticket_record(
            self.member, self.event_instance_ticket.product, is_standby=True
        )

        self.assertFalse(ticket_record.is_refunded())
        self.assertTrue(ticket_record.is_refundable_by_self())
        self.assertTrue(ticket_record.is_refundable_by_admin())
        self.assertTrue(ticket_record.is_stand_by)

        ticket_record.process_refund(self.admin)

        self.assertTrue(ticket_record.is_refunded())
        self.assertFalse(ticket_record.is_refundable_by_self())
        self.assertFalse(ticket_record.is_refundable_by_admin())
        self.assertFalse(ticket_record.is_stand_by)

        # A sale which is not refundable should raise an exception
        self.assertRaises(InvalidTicketRecordError, ticket_record.process_refund, None)

        # Create a ticket record that is not refundable by self, and check that it can be refunded by admin, but not by self
        ticket_record_not_refundable_by_user, _ = self.helper_create_ticket_record(
            self.member, self.event_instance_not_refundable_by_user_product, is_standby=False
        )
        self.assertFalse(ticket_record_not_refundable_by_user.is_refundable_by_self())
        self.assertTrue(ticket_record_not_refundable_by_user.is_refundable_by_admin())

        with self.assertRaises(InvalidTicketRecordError):
            ticket_record_not_refundable_by_user.process_refund(None)

        try:
            ticket_record_not_refundable_by_user.process_refund(self.admin)
        except InvalidTicketRecordError:
            self.fail("Admin should be able to refund a ticket that is not refundable by self.")

    # Self refunding has more constraints than admin refunding, due to final refund time
    def test_tr_is_refundable_by_self(self):
        ticket_record_not_refundable_by_user, _ = self.helper_create_ticket_record(
            self.member, self.event_instance_not_refundable_by_user_product, is_standby=False
        )
        self.assertFalse(ticket_record_not_refundable_by_user.is_refundable_by_self())
        self.assertTrue(ticket_record_not_refundable_by_user.is_refundable_by_admin())

    def test_tr_get_stand_by_queue_position(self):
        # Create 5 ticket records that are stand by
        ticket_records: list[TicketRecord] = []
        for i in range(5):
            ticket_record, _ = self.helper_create_ticket_record(
                self.member, self.event_instance_ticket.product, is_standby=True
            )
            ticket_records.append(ticket_record)

        for i, ticket_record in enumerate(ticket_records):
            self.assertEqual(ticket_record.get_stand_by_queue_position(), i + 1)

    def test_tr_ticket_record_issue_stand_by_ticket(self):
        # Create two ticket records that are stand by
        ticket_record_1, _ = self.helper_create_ticket_record(
            self.member, self.event_instance_ticket.product, is_standby=True
        )
        ticket_record_2, _ = self.helper_create_ticket_record(
            self.member, self.event_instance_ticket.product, is_standby=True
        )

        # Issue a stand by ticket, which should update the first ticket since it was purchased first.
        TicketRecord._issue_stand_by_ticket(ticket_record_1.ticket.event_instance)

        ticket_record_1.refresh_from_db()
        ticket_record_2.refresh_from_db()
        self.assertFalse(ticket_record_1.is_stand_by)
        self.assertTrue(ticket_record_2.is_stand_by)

        # Issue a stand by ticket again, which should not update the second since the stand by limit is 1
        TicketRecord._issue_stand_by_ticket(ticket_record_1.ticket.event_instance)

        ticket_record_1.refresh_from_db()
        ticket_record_2.refresh_from_db()
        self.assertFalse(ticket_record_1.is_stand_by)
        self.assertTrue(ticket_record_2.is_stand_by)

    def test_tr_get_member_purchases(self):
        # Create a ticket record with a sale and one that is admin issued, and check that both are returned when getting member purchases.

        # Alsp create a ticket that does not belong to the member, which should not be returned when getting member purchases
        ticket_record_sale, _ = self.helper_create_ticket_record(self.member, self.event_instance_ticket.product)
        ticket_record_admin = TicketRecord.objects.create(
            ticket=self.event_instance_ticket,
            admin_issued_by=self.admin,
            admin_issued_to=self.member,
        )

        member_purchases = TicketRecord.get_member_purchases(self.member)

        self.assertIn(ticket_record_sale, member_purchases)
        self.assertIn(ticket_record_admin, member_purchases)
        self.assertEqual(member_purchases.count(), 2)

    def test_t_is_product_a_ticket(self):
        ticket = Ticket.is_product_a_ticket(self.event_instance_ticket.product)
        self.assertIsNotNone(ticket)
        assert ticket is not None
        self.assertEqual(ticket.pk, self.event_instance_ticket.pk)
        other_product = Product.objects.create(name="Other Product", price=100, active=True)
        ticket = Ticket.is_product_a_ticket(other_product)
        self.assertIsNone(ticket)

    def test_t_get_stand_by_records(self):
        # Create 5 ticket records that are stand by and 5 that are not, and check that only the stand by ones are returned
        stand_by_records: list[TicketRecord] = []
        for i in range(5):
            ticket_record, _ = self.helper_create_ticket_record(
                self.member, self.event_instance_ticket.product, is_standby=True
            )
            stand_by_records.append(ticket_record)

        for i in range(5):
            ticket_record, _ = self.helper_create_ticket_record(
                self.member, self.event_instance_ticket.product, is_standby=False
            )

        retrieved_stand_by_records = self.event_instance_ticket.get_stand_by_records()

        self.assertCountEqual(retrieved_stand_by_records, stand_by_records)

        for i, record in enumerate(retrieved_stand_by_records):
            self.assertTrue(record.is_stand_by)
            self.assertEqual(record.pk, stand_by_records[i].pk)

    def test_t_next_bought_should_be_stand_by_due_to_ticket_quantity(self):
        # Create a ticket record with a sale, which should not be on standby, since quantity is 1 and this is the first purchase
        next_should_be_standby = self.event_instance_ticket.next_bought_should_be_stand_by_due_to_ticket_quantity()
        self.assertFalse(next_should_be_standby)

        ticket_record, _ = self.helper_create_ticket_record(self.member, self.event_instance_ticket.product)

        # Create another ticket record with a sale, which should be on standby, since quantity is 1 and this is the second purchase
        next_should_be_standby = self.event_instance_ticket.next_bought_should_be_stand_by_due_to_ticket_quantity()
        self.assertTrue(next_should_be_standby)

    def test_t_next_bought_should_be_stand_by(self):
        # Test this is true when capacity is violated
        # Create a ticket record with a sale, which should not be on standby, since quantity is 2 and capacity is 1, but this is the first purchase
        next_should_be_standby = self.low_capcity_ticket.next_bought_should_be_stand_by()
        self.assertFalse(next_should_be_standby)

        ticket_record, _ = self.helper_create_ticket_record(self.member, self.low_capcity_ticket.product)
        self.assertFalse(ticket_record.is_stand_by)

        # Create another ticket record with a sale, which should be on standby, since quantity is 2 and capacity is 1, and this is the second purchase
        next_should_be_standby = self.low_capcity_ticket.next_bought_should_be_stand_by()
        self.assertTrue(next_should_be_standby)

        # Test this is true when quantity is violated
        # Create a ticket record with a sale, which should not be on standby, since quantity is 1 and this is the first purchase
        next_should_be_standby = self.event_instance_ticket.next_bought_should_be_stand_by()
        self.assertFalse(next_should_be_standby)

        ticket_record_3, _ = self.helper_create_ticket_record(self.member, self.event_instance_ticket.product)
        self.assertFalse(ticket_record_3.is_stand_by)

        # Create another ticket record with a sale, which should be on standby, since quantity is 1 and this is the second purchase
        next_should_be_standby = self.event_instance_ticket.next_bought_should_be_stand_by()
        self.assertTrue(next_should_be_standby)

    def test_t_save(self):
        # Test that saving a ticket with a product that is already associated with another ticket throws an exception, since a product can only be associated with one ticket
        with self.assertRaises(InvalidTicketError):
            Ticket.objects.create(event_instance=self.event_instance, quantity=1, product=self.event_instance_product)

        # Test that saving a ticket with a product that is not associated with another ticket does not throw an exception
        try:
            new_product = Product.objects.create(name="New Product", price=100, active=True)
            Ticket.objects.create(event_instance=self.event_instance, quantity=1, product=new_product)
        except InvalidTicketError:
            self.fail(
                "InvalidTicketError was raised when creating a Ticket with a product that is not associated with another ticket, which should be allowed."
            )

    def test_ei_get_name(self):
        # If name overwrite is set, it should return that
        self.assertEqual(self.event_instance.get_name(), self.event_instance.name_overwrite)

        # If name overwrite is not set, it should return the event name
        self.assertEqual(self.event_instance_2.get_name(), self.event.name)

    def test_ei_get_tickets(self):
        tickets = self.event_instance.get_tickets()

        self.assertEqual(tickets.count(), 2)

        Ticket.objects.create(
            event_instance=self.event_instance,
            quantity=1,
            product=Product.objects.create(name="Another Product", price=100, active=True),
        )

        tickets = self.event_instance.get_tickets()
        self.assertEqual(tickets.count(), 3)

    def test_ei_next_bought_ticket_should_be_stand_by_due_to_capacity(self):
        # Create a ticket record with a sale, which should not be on standby, since quantity is 2 and capacity is 1, but this is the first purchase
        next_should_be_standby = (
            self.event_instance_low_capacity.next_bought_ticket_should_be_stand_by_due_to_capacity()
        )
        self.assertFalse(next_should_be_standby)

        ticket_record, _ = self.helper_create_ticket_record(self.member, self.low_capcity_ticket.product)
        self.assertFalse(ticket_record.is_stand_by)

        # Create another ticket record with a sale, which should be on standby, since quantity is 2 and capacity is 1, and this is the second purchase
        next_should_be_standby = (
            self.event_instance_low_capacity.next_bought_ticket_should_be_stand_by_due_to_capacity()
        )
        self.assertTrue(next_should_be_standby)

    def test_ei_get_stand_by_and_issued_ticket_records(self):
        # Create 5 ticket records that are stand by and 5 that are not, and check that only the stand by ones are returned
        stand_by_records: list[TicketRecord] = []
        for i in range(5):
            ticket_record, _ = self.helper_create_ticket_record(
                self.member, self.event_instance_ticket.product, is_standby=True
            )
            stand_by_records.append(ticket_record)

        non_stand_by_records: list[TicketRecord] = []
        for i in range(5):
            ticket_record, _ = self.helper_create_ticket_record(
                self.member, self.event_instance_ticket.product, is_standby=False
            )
            non_stand_by_records.append(ticket_record)

        retrieved_stand_by_records = self.event_instance.get_stand_by_ticket_records()

        self.assertCountEqual(retrieved_stand_by_records, stand_by_records)

        for i, record in enumerate(retrieved_stand_by_records):
            self.assertTrue(record.is_stand_by)
            self.assertEqual(record.pk, stand_by_records[i].pk)

        retrieved_issued_records = self.event_instance.get_issued_ticket_records()

        self.assertCountEqual(retrieved_issued_records, non_stand_by_records)

        for i, record in enumerate(retrieved_issued_records):
            self.assertFalse(record.is_stand_by)
            self.assertEqual(record.pk, non_stand_by_records[i].pk)

    def test_ei_get_non_refunded_ticket_records(self):
        # Create 5 ticket records that are refunded and 5 that are not, and check that only the non-refunded ones are returned
        non_refunded_records: list[TicketRecord] = []
        for i in range(5):
            ticket_record, sale = self.helper_create_ticket_record(self.member, self.event_instance_ticket.product)
            non_refunded_records.append(ticket_record)

        for i in range(5):
            ticket_record, sale = self.helper_create_ticket_record(self.member, self.event_instance_ticket.product)
            sale.refunded_at = timezone.now()
            sale.save()

        retrieved_non_refunded_records = self.event_instance.get_non_refunded_ticket_records()

        self.assertCountEqual(retrieved_non_refunded_records, non_refunded_records)

        for i, record in enumerate(retrieved_non_refunded_records):
            self.assertFalse(record.is_refunded())
            self.assertEqual(record.pk, non_refunded_records[i].pk)

    def test_ei_refund_all_tickets(self):
        # Create 5 ticket records that are not refunded, call the method and check that they are all refunded
        ticket_records: list[TicketRecord] = []
        for i in range(5):
            ticket_record, _ = self.helper_create_ticket_record(self.member, self.event_instance_ticket.product)
            ticket_records.append(ticket_record)

        self.event_instance.refund_all_tickets(self.admin)

        for ticket_record in ticket_records:
            ticket_record.refresh_from_db()
            self.assertTrue(ticket_record.is_refunded())

    def test_ei_refund_all_stand_by_tickets(self):
        # Create 5 ticket records that are stand by, call the method and check that they are all refunded, and 1 that is not stand by, which should not be refunded
        stand_by_records: list[TicketRecord] = []
        for i in range(5):
            ticket_record, _ = self.helper_create_ticket_record(
                self.member, self.event_instance_ticket.product, is_standby=True
            )
            stand_by_records.append(ticket_record)

        non_stand_by_record, _ = self.helper_create_ticket_record(
            self.member, self.event_instance_ticket.product, is_standby=False
        )

        self.event_instance.refund_all_stand_by_tickets(self.admin)

        for ticket_record in stand_by_records:
            ticket_record.refresh_from_db()
            self.assertTrue(ticket_record.is_refunded())

        self.assertFalse(non_stand_by_record.is_refunded())


class TicketFrontendTests(TestCase):
    fixtures = ["initial_data"]

    def test_standby_ticket_is_marked_as_standby_in_frontend(self):
        # Create a ticket record that is stand by
        member = Member.objects.create(username="test", email="test@example.com", balance=10000)
        event = Event.objects.create(name="Test Event", description="This is a test event.")
        event_instance = EventInstance.objects.create(
            event=event,
            name_overwrite="Test Event Instance",
            description_overwrite="This is a test event instance.",
            capacity=1,
            start_time=timezone.now(),
            end_time=timezone.now() + datetime.timedelta(hours=2),
            final_refund_time=timezone.now() + datetime.timedelta(hours=10),
            location="Test Location",
        )
        product = Product.objects.create(name="Test Product", price=100, active=True)
        ticket = Ticket.objects.create(event_instance=event_instance, quantity=1, product=product)

        # Get the menu
        response = self.client.post(reverse('menu_index', args=(1,)))
        # Test that the note is not in the menu
        self.assertNotContains(response, "På standby")

        self.assertFalse(ticket.next_bought_should_be_stand_by())
        sale = Sale.objects.create(member=member, product=product, price=100)
        ticket_record = TicketRecord.objects.filter(sale=sale).first()
        self.assertIsNotNone(ticket_record)
        assert ticket_record is not None
        self.assertFalse(ticket_record.is_stand_by)

        # Get the menu
        response = self.client.post(reverse('menu_index', args=(1,)))

        # Test that the note is in the menu
        self.assertContains(response, "På standby")

        self.assertTrue(ticket.next_bought_should_be_stand_by())
        sale = Sale.objects.create(member=member, product=product, price=100)
        ticket_record = TicketRecord.objects.filter(sale=sale).first()

        self.assertIsNotNone(ticket_record)
        assert ticket_record is not None
        self.assertTrue(ticket_record.is_stand_by)
