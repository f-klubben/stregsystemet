from django import forms
from django_select2 import forms as s2forms
from stregsystem.models import Category


class CategoryReportForm(forms.Form):
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        required=True,
        label="Category",
        widget=s2forms.ModelSelect2MultipleWidget(
            model=Category,
            search_fields=["name__icontains"],
            max_results=500,
            queryset=Category.objects.all(),
        ),
    )
