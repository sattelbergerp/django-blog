from django.test import TestCase
from django.contrib.auth.models import User
from .models import Author, Tag
from django.db.utils import IntegrityError
# Create your tests here.

class AuthorModelTest(TestCase):

    def test_author_created_when_user_created(self):
       user = User(username="test_user", password="test_pass")
       user.save()
       self.assertTrue(user.author)

    def test_author_created_hidden(self):
       user = User(username="test_user", password="test_pass")
       user.save()
       self.assertFalse(user.author.visible)

    def test_author_generates_correct_slug(self):
       user = User(username="test#_$user%$^&", password="test_pass")
       user.save()
       self.assertEqual(user.author.slug, 'test_user')

    def test_deleting_user_deletes_author(self):
       user = User(username="test#_$user%$^&", password="test_pass")
       user.save()
       self.assertEqual(Author.objects.count(), 1)
       user.delete()
       self.assertEqual(Author.objects.count(), 0)

    def test_creating_author_without_user_fails(self):
        author = Author()
        self.assertRaises(IntegrityError, author.save)

class TagModelTest(TestCase):

    def test_tag_generates_correct_slug(self):
        tag = Tag(name='Test Tag!')
        tag.save()
        self.assertEqual(tag.slug, 'test-tag')
