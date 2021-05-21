from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.conf import settings
from blog.forms import BaseUserForm

class SignupForm(BaseUserForm):
    pass