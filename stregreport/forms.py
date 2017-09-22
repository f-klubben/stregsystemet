from django import forms

from stregsystem.models import (Category, Product)

class CategoryReportForm(forms.Form):
    categories = forms.ModelMultipleChoiceField(
        required=True,
        queryset=Category.objects.all()
    )
