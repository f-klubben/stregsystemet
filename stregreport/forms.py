from django import forms
from django_select2 import forms as s2forms

from stregsystem.models import Category


class CategoryReportForm(forms.Form):
    categories = forms.ModelMultipleChoiceField(
        required=True,
        label="Category",
        widget=s2forms.ModelSelect2MultipleWidget(
            search_fields=["name__icontains"],
        ),
        queryset=Category.objects.all()
    )
