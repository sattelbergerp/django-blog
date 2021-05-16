import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "blog_project.settings")
import django
django.setup()
from blog.models import Post, Comment, Author
from django.contrib.auth.models import User