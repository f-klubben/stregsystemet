from django.forms.widgets import Input

from stregsystem.models import Member


class ReadonlyFemberInput(Input):
    template_name = 'admin/stregsystem/widgets/readonly_fember_input.html'

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["fember"] = None
        if value is not None:
            members = Member.objects.filter(pk=value)
            if members.exists():
                context["fember"] = members.get()
        return context
