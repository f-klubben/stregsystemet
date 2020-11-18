from django import forms


class QRPaymentForm(forms.Form):
    member = forms.CharField(max_length=16)
    amount = forms.IntegerField(min_value=50, required=False)

    
class PurchaseForm(forms.Form):
    product_id = forms.IntegerField()
