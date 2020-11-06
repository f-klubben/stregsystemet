from django.forms.widgets import Input

from stregsystem.models import Member
from stregsystem.templatetags.stregsystem_extras import money


class ReadonlyFemberInput(Input):
    template_name = 'admin/stregsystem/widgets/readonly_fember_input.html'

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["fember"] = None
        if value is not None:
            member = Member.objects.filter(pk=value)
            if member.exists():
                m = member.get()
                context["fember"] = f"({money(m.balance)}) {m.firstname} {m.lastname} - {m.username}"
        return context
