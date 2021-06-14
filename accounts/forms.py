from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.conf import settings
import string
from django.utils.translation import gettext as _
from django.contrib.auth.password_validation import validate_password

class BaseUserForm(forms.ModelForm):
    confirm_password = forms.CharField(max_length=User.password.field.max_length, required=True)
    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        super().clean()
        password = self.cleaned_data.get('password')
        if password != self.cleaned_data.get('confirm_password'):
            self.add_error('confirm_password', _('Passwords must match'))
            self.add_error('password', _('Passwords must match'))

        if password:
            validate_password(password, user=getattr(self, 'user', None))
            

class SignupForm(BaseUserForm):
    pass