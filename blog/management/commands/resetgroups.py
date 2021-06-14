from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group

class Command(BaseCommand):
    help = 'Reset that author and moderator groups'
    requires_migrations_checks = True

    def handle(self, *args, **options):
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
