from django.core.management.base import BaseCommand, CommandError
from blog.models import Comment

class Command(BaseCommand):
    help = 'Validate cached vote totals match actual vote counts'
    requires_migrations_checks = True

    def handle(self, *args, **options):
        comments = Comment.objects.all()
        total, failed = comments.count(), 0
        self.stdout.write('Validating comments...')
        for i, comment in enumerate(comments):
            self.stdout.write(f'\r{i+1}/{total}', ending='')
            if comment.votes != comment.get_computed_votes():
                self.stdout.write(f'\r{i+1}/{total} Missmatch found on comment id {comment.id} expected {comment.get_computed_votes()} got {comment.votes}')
                comment.votes = comment.get_computed_votes()
                failed += 1
                comment.save()
        
        self.stdout.write(f'\n{failed} of {total} comment(s) failed to validate')