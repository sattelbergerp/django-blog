from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Author, Tag, Post
from django.db.utils import IntegrityError

#Model tests
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

#View tests
class PostsIndexViewTest(TestCase):

    def setUp(self):
        self.user = User(username='test_user', password='test_pass')
        self.user.save()

    def test_post_index_responds_with_posts(self):
        posts = [Post(title=f'test_title_{i}', content=f'test_content_{i}', author=self.user.author) for i in range(5)]
        for post in posts:
            post.save()
        resp = self.client.get(reverse('blog:posts_index'))
        self.assertEquals(resp.status_code, 200)
        for i in range(5):
            self.assertContains(resp.title)
            self.assertContains(resp.content)

    def test_post_index_truncates_long_title_and_text(self):
        post = Post(title=str([f't{i}' for i in range(100)]), content=str([f't{i}' for i in range(500)]), author=self.user.author)
        post.save()
        resp = self.client.get(reverse('blog:posts_index'))
        self.assertEquals(resp.status_code, 200)
        self.assertNotContains(post.title)
        self.assertNotContains(post.text)