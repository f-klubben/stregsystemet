

from django.dispatch import receiver
from stregsystem.signals import on_new_sale
from stregsystem.models import Product, Sale

from events.models import Ticket, TicketRecord

@receiver(on_new_sale)
def handle_new_sale(sender: Sale, **kwargs):

    if not isinstance(sender, Sale):
        raise TypeError("Sender must be an instance of Sale")

    product = kwargs.get("product")

    if not product:
        raise ValueError("No product provided in on_new_sale signal")
    if not isinstance(product, Product):
        raise TypeError("Product must be an instance of Product")

    ticket = Ticket.is_product_a_ticket(product)
    if ticket:
        TicketRecord.create_from_sale_and_ticket(sender, ticket)
