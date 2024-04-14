from django.db import transaction

from stregsystem.models import Reimbursement, Sale, SaleNotFoundError, Payment


@transaction.atomic
def reimburse_sale(sale_id):
    """
    1. Create payment to pay back the member
    2. Create reimbursement object referencing the payment and the product
    3. Adjust the inventory
    4. delete the sale
    """
    sale: Sale = Sale.objects.get(id=sale_id)
    if not sale:
        raise SaleNotFoundError()
    product = sale.product
    product.quantity = product.quantity + 1

    sale.member.balance = sale.member.balance + sale.price
    sale.member.save()

    Sale.delete(sale)
    reimbursement = Reimbursement(product=product, amount=sale.price, member=sale.member)
    reimbursement.save()
