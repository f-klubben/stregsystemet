import django.forms

from stregsystem.models import MobilePayment, Member
from django_select2 import forms as s2forms


class Select2MemberWidget(s2forms.ModelSelect2Widget):
    search_fields = ['username__icontains', 'firstname__icontains', 'lastname__icontains', 'email__icontains']
    model = Member


class MobilePayToolForm(django.forms.ModelForm):
    class Meta:
        model = MobilePayment
        fields = ('amount', 'member', 'member_guess', 'customer_name', 'comment')
        widgets = {"member": Select2MemberWidget,
                   "status": django.forms.RadioSelect()}

    def __init__(self, *args, **kwargs):
        super(MobilePayToolForm, self).__init__(*args, **kwargs)
        if self.instance.id:

            for field in self.fields:
                if field in ['amount', 'member_guess', 'customer_name', 'comment']:
                    self.fields[field].widget.attrs['readonly'] = True
                    self.fields[field].widget.attrs['disabled'] = True
