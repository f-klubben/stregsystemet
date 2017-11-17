import ldap

from django.shortcuts import render
from stregsystem.models import Member
from .forms import MemberForm


def _add_ldap(member):
    l = ldap.open("fklub.dk")
    l.protocol_version = ldap.VERSION3

    l.simple_bind("", "")
    l.add_s("test", "test")


def index(request):
    if request.method == "POST":
        form = MemberForm(request.POST)
        if form.is_valid():
            newMember = form.save(commit=False)
            if not Member.objects.filter(username=newMember.username).exists():
                newMember.save()
                _add_ldap(newMember)
                form = MemberForm()
                return render(request, 'registration/base.html', {
                    "form": form,
                    "messages": [
                        "New member created",
                    ],
                })
            form.add_error("username", "Username already taken")
    else:
        form = MemberForm()
    return render(request, 'registration/base.html', {"form": form})
