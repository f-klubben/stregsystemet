import datetime

from django import forms

from stregsystem.models import MobilePayment, Member
from django_select2 import forms as s2forms


class Select2MemberWidget(s2forms.ModelSelect2Widget):
    search_fields = ['username__icontains', 'firstname__icontains', 'lastname__icontains', 'email__icontains']
    model = Member


class MobilePayToolForm(forms.ModelForm):
    class Meta:
        model = MobilePayment
        fields = ('timestamp', 'amount', 'member', 'customer_name', 'comment', 'status')
        widgets = {"member": Select2MemberWidget, "status": forms.RadioSelect(choices=MobilePayment.STATUS_CHOICES)}

    def __init__(self, *args, **kwargs):
        super(MobilePayToolForm, self).__init__(*args, **kwargs)
        # Make fields not meant for editing by user readonly (note that this is prevented in template as well)
        if self.instance.id:
            for field in self.fields:
                if field in ['amount', 'customer_name', 'comment']:
                    self.fields[field].widget.attrs['readonly'] = True


class QRPaymentForm(forms.Form):
    member = forms.CharField(max_length=16)
    amount = forms.IntegerField(min_value=50, required=False)


class PurchaseForm(forms.Form):
    product_id = forms.IntegerField()


class RankingDateForm(forms.Form):
    from_date = forms.DateField(widget=forms.SelectDateWidget(years=range(2000, datetime.date.today().year + 1)))
    to_date = forms.DateField(
        initial=datetime.date.today(), widget=forms.SelectDateWidget(years=range(2000, datetime.date.today().year + 1))
    )

    # validate form. make sure that from_date is before to_date
    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data['from_date'] > cleaned_data['to_date']:
            # raise forms.ValidationError('Fra dato skal være før eller lig til dato')
            self.add_error('to_date', 'Fra dato skal være før eller lig til dato')
        return cleaned_data
