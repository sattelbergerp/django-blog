from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.conf import settings
from .models import Author

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
                self.add_error('password', 'Password must be at least 8 characters long')

class UserSettingsForm(BaseUserForm):
    password = forms.CharField(max_length=User.password.field.max_length, required=False)
    confirm_password = forms.CharField(max_length=User.password.field.max_length, required=False)
    current_password = forms.CharField(max_length=User.password.field.max_length, required=False)
    
    def __init__(self, *args, **kwargs):
        if not 'user' in kwargs:
            raise AttributeError('User cannot be None')
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password']

    def clean(self):
        super().clean()
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        current_password = self.cleaned_data.get('current_password')
        email = self.cleaned_data.get('email')

        if password or email != self.user.email:
            if not current_password:
                self.add_error('current_password', 'Required to change username or password')
            elif not authenticate(username=self.user.username, password=current_password):
                self.add_error('current_password', 'Password is incorrect')

class AuthorSettingsForm(forms.ModelForm):
    author_enabled = forms.BooleanField()
    moderator = forms.BooleanField()

    class Meta:
        model = Author
        fields = ['bio']