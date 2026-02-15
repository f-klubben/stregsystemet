from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages


class CustomLoginView(View):
    template_name = 'sso/login.html'

    def get(self, request):
        # Get the 'next' parameter from the URL
        next_url = request.GET.get('next', '/')

        context = {
            'next': next_url,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        username = request.POST.get('username')
        next_url = request.POST.get('next', '/')

        user = authenticate(request, username=username)

        if user is not None:
            login(request, user)
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password')
            context = {
                'next': next_url,
                'username': username,  # Preserve username on error
            }
            return render(request, self.template_name, context)
