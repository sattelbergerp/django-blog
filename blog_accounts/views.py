from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import CreateView
from django.contrib.auth.models import User
from django.contrib.auth import login
from .forms import SignupForm

# Create your views here.

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(form.cleaned_data['username'], form.cleaned_data['email'], form.cleaned_data['password'])
            user.save()
            login(request, user)
            return HttpResponseRedirect('/')
    else:
       form = SignupForm()
    return render(request, 'blog_accounts/signup.html', {'form': form})

    

