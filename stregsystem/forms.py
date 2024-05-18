import datetime

from django import forms

from stregsystem.models import MobilePayment, Member, ApprovalModel, PendingSignup
from django_select2 import forms as s2forms


class Select2MemberWidget(s2forms.ModelSelect2Widget):
    search_fields = ['username__icontains', 'firstname__icontains', 'lastname__icontains', 'email__icontains']
    model = Member


class ApprovalToolForm(forms.ModelForm):
    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].widget = forms.RadioSelect(choices=ApprovalModel.STATUS_CHOICES)


class MobilePayToolForm(ApprovalToolForm):
    class Meta:
        model = MobilePayment
        fields = ('timestamp', 'amount', 'member', 'customer_name', 'comment', 'status')
        widgets = {"member": Select2MemberWidget}

    def __init__(self, *args, **kwargs):
        super(MobilePayToolForm, self).__init__(*args, **kwargs)

        # Remove 'Rejected' as it has no implemented behavior
        self.fields['status'].widget.choices = ApprovalModel.STATUS_CHOICES[:-1]

        # Make fields not meant for editing by user readonly (note that this is prevented in template as well)
        if self.instance.id:
            for field in self.fields:
                if field in ['amount', 'customer_name', 'comment', 'timestamp']:
                    self.fields[field].widget.attrs['readonly'] = True


class SignupToolForm(ApprovalToolForm):
    class Meta:
        model = PendingSignup
        fields = ('due', 'member', 'status')

    def __init__(self, *args, **kwargs):
        super(SignupToolForm, self).__init__(*args, **kwargs)

        for field in self.fields:
            if field in ['due', 'member']:
                self.fields[field].widget.attrs['readonly'] = True


class QRPaymentForm(forms.Form):
    member = forms.CharField(max_length=16)
    amount = forms.DecimalField(min_value=50, decimal_places=2, required=False)


class PurchaseForm(forms.Form):
    product_id = forms.IntegerField()


class SignupForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ('username', 'email', 'firstname', 'lastname', 'gender')
        widgets = {
            'username': forms.TextInput(attrs={'autocomplete': "off"}),
            'email': forms.TextInput(attrs={'autocomplete': "off"}),
            'firstname': forms.TextInput(attrs={'autocomplete': "off"}),
            'lastname': forms.TextInput(attrs={'autocomplete': "off"}),
            'gender': forms.Select(),
        }
        labels = {
            'username': "Brugernavn",
            'email': "E-Mail",
            'firstname': "Fornavn",
            'lastname': "Efternavn",
            'gender': 'Biologisk køn',
        }
        error_messages = {
            'username': {
                'required': 'Udfyldning af `Brugernavn` er påkrævet.',
                'max_length': 'Længden af `Brugernavn` må ikke overstige 16 tegn.',
            },
            'firstname': {
                'required': 'Udfyldning af `Fornavn` er påkrævet.',
                'max_length': 'Længden af `Fornavn` må ikke overstige 16 tegn.',
            },
            'lastname': {
                'required': 'Udfyldning af `Efternavn` er påkrævet.',
                'max_length': 'Længden af `Efternavn` må ikke overstige 16 tegn.',
            },
        }


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
