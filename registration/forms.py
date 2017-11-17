from django import forms
from stregsystem.models import Member


class MemberForm(forms.ModelForm):
    error_css_class = 'error'
    class Meta:
        model = Member
        exclude = ("want_spam", "balance", "undo_count", "notes", "active")
