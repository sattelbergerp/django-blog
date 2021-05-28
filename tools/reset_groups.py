import os
import sys
import inspect

sys.path.insert(1, os.path.join(sys.path[0], '..')) #Set python to resolve imports from parent directory (project root)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "blog_project.settings")
import django
django.setup()
from django.contrib.auth.models import Group, Permission

try:
    author_group = Group.objects.get(name='author')
    author_group.delete()
    print('Author group removed.')
except Group.DoesNotExist:
    print('Author group does not exist (No action necessary).')

try:
    moderator_group = Group.objects.get(name='moderator')
    moderator_group.delete()
    print('Moderator group removed.')
except Group.DoesNotExist:
    print('Moderator group does not exist (No action necessary).')
