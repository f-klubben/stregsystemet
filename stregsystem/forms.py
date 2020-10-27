import django.forms

from stregsystem.models import MobilePayment, Member
from django_select2 import forms as s2forms


class Select2MemberWidget(s2forms.ModelSelect2Widget):
    search_fields = ['username__icontains', 'firstname__icontains', 'lastname__icontains', 'email__icontains']
    model = Member


class MobilePayToolForm(django.forms.ModelForm):
    class Meta:
        model = MobilePayment
        fields = ('amount', 'member', 'member_guess', 'customer_name', 'comment', 'status')
        widgets = {"member": Select2MemberWidget,
                   "member_guess": django.forms.TextInput,  # hidden field but widget chosen for performance
                   "status": django.forms.RadioSelect(choices=MobilePayment.STATUS_CHOICES)}

    def __init__(self, *args, **kwargs):
        super(MobilePayToolForm, self).__init__(*args, **kwargs)
        # Make fields not meant for editing by user readonly (note that this is prevented in template as well)
        if self.instance.id:
            for field in self.fields:
                if field in ['amount', 'member_guess', 'customer_name', 'comment']:
                    self.fields[field].widget.attrs['readonly'] = True
