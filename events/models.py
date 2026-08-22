from __future__ import annotations

from typing import Optional

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from stregsystem.models import Product, Sale, Member
from stregsystem.utils import (
    get_bool_pretty,
)


class InvalidTicketRecordError(Exception):
    pass


class InvalidTicketError(Exception):
    pass


class Event(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()
    image = models.ImageField(upload_to="event_images/", blank=True, null=True)

    def __str__(self):
        return self.name


class EventInstance(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="instances", null=False, blank=False)
    name_overwrite = models.CharField(max_length=50, blank=True)
    description_overwrite = models.TextField(blank=True)
    image_overwrite = models.ImageField(upload_to="event_instance_images/", blank=True, null=True)
    capacity = models.IntegerField(null=False, blank=False)
    start_time = models.DateTimeField(null=False, blank=False)
    end_time = models.DateTimeField(null=False, blank=False)
    final_refund_time = models.DateTimeField(null=False, blank=False)
    location = models.CharField(max_length=100, null=False, blank=False)

    def get_name(self):
        if self.name_overwrite:
            return self.name_overwrite
        else:
            return self.event.name

    def get_tickets(self):
        return Ticket.objects.filter(event_instance=self)

    def next_bought_ticket_should_be_stand_by_due_to_capacity(self) -> bool:
        # If the number of tickets sold for this event instance has reached the capacity for this event instance, the next bought ticket should be put on stand-by
        ticket_sales_count = self.get_issued_ticket_records().count()
        return ticket_sales_count >= self.capacity

    # Gets all stand by ticket record for all ticket types of this event instance, ordered by sale timestamp (oldest first)
    def get_stand_by_ticket_records(self):
        return TicketRecord.objects.filter(
            ticket__event_instance=self,
            is_stand_by=True,
        ).order_by('sale__timestamp')

    def get_issued_ticket_records(self):
        return TicketRecord.objects.filter(
            ticket__event_instance=self,
            is_stand_by=False,
            sale__refunded_at__isnull=True,
        ).order_by('sale__timestamp')

    def get_non_refunded_ticket_records(self):
        return TicketRecord.objects.filter(
            ticket__event_instance=self,
            sale__refunded_at__isnull=True,
        )

    def refund_all_tickets(self, admin_user: User) -> None:
        for ticket_record in self.get_non_refunded_ticket_records():
            ticket_record.process_refund(admin_user)

    def refund_all_stand_by_tickets(self, admin_user: User) -> None:
        for ticket_record in self.get_stand_by_ticket_records():
            ticket_record.process_refund(admin_user)

    def __str__(self):
        return f"{self.name_overwrite} ({self.from_start_to_end_time_str()})"

    def from_start_to_end_time_str(self):
        return f"Fra {self.start_time.strftime('%d/%m/%Y %H:%M')} - til {self.end_time.strftime('%d/%m/%Y %H:%M')}"


class Ticket(models.Model):
    event_instance = models.ForeignKey(EventInstance, on_delete=models.CASCADE, related_name="tickets")
    name = models.CharField(max_length=50)
    description = models.TextField()
    quantity = models.IntegerField()
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="tickets")

    @staticmethod
    def is_product_a_ticket(product: Product) -> Optional[Ticket]:
        ticket = Ticket.objects.filter(product=product).first()
        return ticket

    def get_stand_by_records(self) -> models.QuerySet[TicketRecord]:
        return TicketRecord.objects.filter(
            ticket=self,
            is_stand_by=True,
        ).order_by('sale__timestamp')

    def next_bought_should_be_stand_by_due_to_ticket_quantity(self) -> bool:
        # If the number of tickets sold for this ticket type has reached the quantity for this ticket, the next bought ticket of this type should be put on stand-by
        ticket_sales_count = self.event_instance.get_issued_ticket_records().count()
        return ticket_sales_count >= self.quantity

    def next_bought_should_be_stand_by(self) -> bool:
        # Count ticket sales for event instance, to determine if the ticket being created should be put on stand-by
        if (
            self.event_instance.next_bought_ticket_should_be_stand_by_due_to_capacity()
            or self.next_bought_should_be_stand_by_due_to_ticket_quantity()
        ):
            return True
        else:
            return False

    def save(self, *args, **kwargs):
        if Ticket.objects.filter(product=self.product).exists():
            raise InvalidTicketError("A product can only be associated with one ticket")
        super(Ticket, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} for {self.event_instance.name_overwrite}"


class TicketRecord(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="purchases")
    sale = models.OneToOneField(Sale, on_delete=models.CASCADE, related_name="ticket_record", blank=True, null=True)

    has_attended = models.BooleanField(null=True, blank=True)
    is_stand_by = models.BooleanField(default=False, null=False)

    admin_issued_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="issued_tickets", null=True)
    admin_issued_to = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="tickets", null=True)

    @staticmethod
    def create_from_sale_and_ticket(sale: Sale, ticket: Ticket) -> None:

        is_stand_by = ticket.next_bought_should_be_stand_by()

        TicketRecord.objects.create(ticket=ticket, sale=sale, is_stand_by=is_stand_by)

    @staticmethod
    def get_member_purchases(member: Member) -> models.QuerySet["TicketRecord"]:
        return TicketRecord.objects.filter(models.Q(sale__member=member) | models.Q(admin_issued_to=member))

    @staticmethod
    def _issue_stand_by_ticket(event_instance: EventInstance) -> None:
        # Get the one stand by ticket of each ticket type, then find the one that has been on stand-by the longest (i.e. has the earliest sale timestamp) and isssue it if possible
        tickets = event_instance.get_tickets()

        # Get the first stand-by ticket record for each ticket type
        stand_by_ticket_records: list[TicketRecord] = []
        for ticket in tickets:
            stand_by_ticket_record = ticket.get_stand_by_records().first()
            if stand_by_ticket_record is not None:
                stand_by_ticket_records.append(stand_by_ticket_record)

        stand_by_due_to_capacity = event_instance.next_bought_ticket_should_be_stand_by_due_to_capacity()

        for stand_by_ticket_record in stand_by_ticket_records:
            if (
                not stand_by_due_to_capacity
                and not stand_by_ticket_record.ticket.next_bought_should_be_stand_by_due_to_ticket_quantity()
            ):
                stand_by_ticket_record.is_stand_by = False
                stand_by_ticket_record.save()

    def get_stand_by_queue_position(self) -> Optional[int]:
        if not self.is_stand_by:
            return None

        # Get all stand-by tickets for the same event instance
        stand_by_tickets = self.ticket.event_instance.get_stand_by_ticket_records()
        # Find the position of this ticket in the queue
        try:
            return list(stand_by_tickets).index(self) + 1
        except ValueError:
            return None

    def process_refund(self, adminUser: Optional[User]) -> None:
        if adminUser is not None:
            if not self.is_refundable_by_admin():
                raise InvalidTicketRecordError("Admin can't refund this ticket")
        elif not self.is_refundable_by_self():
            raise InvalidTicketRecordError("User can't refund this ticket")
        if self.sale is None:
            raise InvalidTicketRecordError("Sale is none, this should have been caught by the is_refundable checks")

        self.is_stand_by = False
        self.save()

        self.sale.process_refund(adminUser)
        TicketRecord._issue_stand_by_ticket(self.ticket.event_instance)

    def is_refundable_by_self(self) -> bool:
        refund_time_passed = self.ticket.event_instance.final_refund_time <= timezone.now()
        return not refund_time_passed and self.is_refundable_by_admin()

    def is_refundable_by_admin(self) -> bool:
        return self.sale is not None and not self.sale.is_refunded()

    def is_refunded(self) -> bool:
        return self.sale is not None and self.sale.is_refunded()

    def get_refunded_pretty(self) -> str:
        return get_bool_pretty(self.is_refunded())

    def get_stand_by_pretty(self) -> str:
        return get_bool_pretty(self.is_stand_by)

    @property
    def get_ticket_owner(self) -> Member:
        if self.sale is not None:
            return self.sale.member
        elif self.admin_issued_to is not None:
            return self.admin_issued_to
        else:
            raise RuntimeError("Ticket has no owner")

    def save(self, *args, **kwargs):
        if self.sale is not None and self.admin_issued_to is not None:
            raise InvalidTicketRecordError("Ticket can't have both a sale and an admin issuer")
        if self.sale is None and self.admin_issued_to is None:
            raise InvalidTicketRecordError("Ticket must have either a sale or an admin issuer")
        if self.sale is not None and self.is_stand_by and self.sale.refunded_at is not None:
            raise InvalidTicketRecordError("Ticket can't be on stand-by if the associated sale is refunded")
        super(TicketRecord, self).save(*args, **kwargs)

    def __str__(self):
        ticket_owner = self.get_ticket_owner
        return f"{ticket_owner.username if ticket_owner else 'No Owner?'}'s billet: {self.ticket.name} (Stand-by: {self.get_stand_by_pretty()}, Refunded: {self.get_refunded_pretty()})"
