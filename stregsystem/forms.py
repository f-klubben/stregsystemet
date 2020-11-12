from django import forms


class PurchaseForm(forms.Form):
    product_id = forms.IntegerField()
