from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.conf import settings
import string
from django.utils.translation import gettext as _

class BaseUserForm(forms.ModelForm):
    confirm_password = forms.CharField(max_length=User.password.field.max_length, required=True)
    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        super().clean()
        password = self.cleaned_data.get('password')
        if password != self.cleaned_data.get('confirm_password'):
            self.add_error('confirm_password', 'Passwords must match')
            self.add_error('password', 'Passwords must match')

        if password and getattr(settings, 'ENFORCE_PASSWORD_VALIDATION', True):
            if len(password) < 8:
                self.add_error('password', _('Password must be at least 8 characters long'))
            num_lowercase, num_uppercase, num_digits, num_special = 0, 0, 0, 0
            for char in password:
                num_lowercase += 1 if char in string.ascii_lowercase else 0
                num_uppercase += 1 if char in string.ascii_uppercase else 0
                num_digits += 1 if char in string.digits else 0
                num_special += 1 if char in string.punctuation else 0
            if not num_lowercase:
                self.add_error('password', _('Password must contain at least one lowercase character'))
            if not num_uppercase:
                self.add_error('password', _('Password must contain at least one uppercase character'))
            if not num_digits:
                self.add_error('password', _('Password must contain at least one number'))
            if not num_special:
                self.add_error('password', _('Password must contain at least one special character'))

class SignupForm(BaseUserForm):
    pass