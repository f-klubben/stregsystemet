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


class SignupForm(forms.Form):
    username = forms.CharField(max_length=16, label='Brugernavn',
                               error_messages={'required': 'Udfyldning af `Brugernavn` er påkrævet.',
                                               'max_length': 'Længden af `Brugernavn må ikke overstige 16 tegn.`'})
    email = forms.EmailField(label='E-Mail')
    firstname = forms.CharField(max_length=20, label='Fornavn',
                                error_messages={'required': 'Udfyldning af `Fornavn` er påkrævet.',
                                                'max_length': 'Længden af `Fornavn må ikke overstige 16 tegn.`'})
    lastname = forms.CharField(max_length=30, label='Efternavn',
                               error_messages={'required': 'Udfyldning af `Efternavn` er påkrævet.',
                                               'max_length': 'Længden af `Efternavn må ikke overstige 16 tegn.`'})
