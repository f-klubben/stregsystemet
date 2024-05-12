from django.db import transaction

from stregsystem.models import Reimbursement, Sale, SaleNotFoundError, ReimbursementTransaction


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
    product.save()
    sale.member.fulfill(ReimbursementTransaction(amount=sale.price))
    sale.member.save()
    sale.save()

    Sale.delete(sale)
    reimbursement = Reimbursement(product=product, amount=sale.price, member=sale.member)
    reimbursement.save()
