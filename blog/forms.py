from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.conf import settings
from .models import Author, Post
from PIL import Image
from django.contrib.humanize.templatetags.humanize import intcomma
import string

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
            num_lowercase, num_uppercase, num_digits, num_special = 0, 0, 0, 0
            for char in password:
                num_lowercase += 1 if char in string.ascii_lowercase else 0
                num_uppercase += 1 if char in string.ascii_uppercase else 0
                num_digits += 1 if char in string.digits else 0
                num_special += 1 if char in string.punctuation else 0
            if not num_lowercase:
                self.add_error('password', 'Password must contain at least one lowercase character')
            if not num_uppercase:
                self.add_error('password', 'Password must contain at least one uppercase character')
            if not num_digits:
                self.add_error('password', 'Password must contain at least one number')
            if not num_special:
                self.add_error('password', 'Password must contain at least one special character')

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
    author_enabled = forms.BooleanField(required=False)
    moderator = forms.BooleanField(required=False)

    class Meta:
        model = Author
        fields = ['bio']

class PostForm(forms.ModelForm):
    tags = forms.CharField(max_length=255, required=False)
    remove_header_image = forms.BooleanField(required=False)

    class Meta:
        model = Post
        fields = ['title', 'header_image', 'content']

    def clean(self):
        super().clean()
        header_image_file = self.cleaned_data.get('header_image')
        if header_image_file:
            with Image.open(header_image_file) as im:
                total_pixels = im.width * im.height
                if total_pixels > 40000000:
                    self.add_error('header_image', f'Image size ({intcomma(total_pixels)} pixels) exceeds limit of 10,000,000 pixels')
