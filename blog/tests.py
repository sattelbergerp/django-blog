from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Author, Tag, Post, Comment
from django.db.utils import IntegrityError
from django.utils import timezone

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

class PostModelTest(TestCase):

    def setUp(self):
        self.user = User(username='test_user', password='test_pass')
        self.user.save()

    def test_has_been_edited_returns_false_for_new_posts(self):
        post = Post(author=self.user.author, title='test', content='test', updated_on=timezone.now() + timedelta(seconds=59))
        post.save()
        self.assertFalse(post.has_been_edited())

    def test_has_been_edited_returns_true_for_edited_posts(self):
        post = Post(author=self.user.author, title='test', content='test')
        post.save()
        post.updated_on=timezone.now() + timedelta(seconds=60)
        self.assertTrue(post.has_been_edited())

#View tests
class PostsIndexViewTest(TestCase):

    def setUp(self):
        self.user = User(username='test_user', password='test_pass')
        self.user.save()
        self.user.author.visible = True
        self.user.author.save()

    def test_post_index_responds_with_posts_ordered_by_creation_date(self):
        day_deltas = [10, -2, 5, 100, 1]
        posts = [Post(title=f'test_title_{i}', content=f'test_content_{i}', author=self.user.author) for i in range(len(day_deltas))]
        for i, post in enumerate(posts):
            post.save()
            post.created_on = timezone.now()-timedelta(days=day_deltas[i])
            post.save()

        resp = self.client.get(reverse('blog:post_index'))
        self.assertEquals(resp.status_code, 200)
        for post in posts:
            self.assertContains(resp, post.title)
            self.assertContains(resp, post.content)
        posts.sort(key=lambda x: x.created_on, reverse=True)
        self.assertQuerysetEqual(posts, resp.context['post_list'])

    def test_post_index_paginates_properly(self):
        posts = [Post(title=f'test_title_{i}', content=f'test_content_{i}', author=self.user.author) for i in range(30)]
        for i, post in enumerate(posts):
            post.save()
            post.created_on = timezone.now()-timedelta(days=i)
            post.save()

        resp = self.client.get(reverse('blog:post_index'))
        for i in range(20):
            self.assertContains(resp, posts[i].title)
            self.assertContains(resp, posts[i].content)

        resp = self.client.get(reverse('blog:post_index'), data={'page': 2})
        for i in range(20, len(posts)):
            self.assertContains(resp, posts[i].title)
            self.assertContains(resp, posts[i].content)

    def test_post_index_hides_posts_from_authors_that_are_not_visible(self):
        posts = []
        for i in range(10):
          user = User(username=f'test_{i}', password=f'test_{i}')
          user.save()
          user.author.visible = (i % 2) == 0
          user.author.save()
          post = Post(title=f'test_title_{i}', content=f'test_content_{i}', author=user.author)
          post.save()
          posts.append(post)

        resp = self.client.get(reverse('blog:post_index'))
        for post in posts:
            if post.author.visible:
                self.assertContains(resp, post.title)
                self.assertContains(resp, post.content)
            else:
                self.assertNotContains(resp, post.title)
                self.assertNotContains(resp, post.content)

    def test_post_index_truncates_long_title_and_text(self):
        post = Post(title=''.join([f't{i}' for i in range(100)]), content=''.join([f't{i}' for i in range(500)]), author=self.user.author)
        post.save()
        resp = self.client.get(reverse('blog:post_index'))
        self.assertEquals(resp.status_code, 200)
        self.assertNotContains(resp, post.title)
        self.assertNotContains(resp, post.content)

class AuthorDetailViewTest(TestCase):

    def setUp(self):
        self.users = []
        for i in range(4):
            user = User(username=f'test_user_{i}', password=f'test_pass_{i}')
            user.save()
            user.author.visible = True
            user.author.bio = f'test_bio_{i}'
            user.author.save()
            self.users.append(user)

    def test_author_detail_returns_not_found(self):
        resp = self.client.get(reverse('blog:author_detail', kwargs={'slug': 'no-author'}))
        self.assertEquals(resp.status_code, 404)

    def test_author_detail_returns_not_found_for_hidden_author(self):
        user = User(username=f'hidden-author', password=f'hidden-author-pass')
        user.save()
        resp = self.client.get(reverse('blog:author_detail', kwargs={'slug': user.author.slug}))
        self.assertEquals(resp.status_code, 404)

    def test_post_index_responds_with_bio_and_posts_ordered_by_creation_date(self):
        day_deltas = [10, -2, 5, 100, 1]
        posts = [Post(title=f'test_title_{i}', content=f'test_content_{i}', author=self.users[0].author) for i in range(len(day_deltas))]
        for i, post in enumerate(posts):
            post.save()
            post.created_on = timezone.now()-timedelta(days=day_deltas[i])
            post.save()

        resp = self.client.get(reverse('blog:author_detail', kwargs={'slug': self.users[0].author.slug}))
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, self.users[0].author.bio)
        for post in posts:
            self.assertContains(resp, post.title)
            self.assertContains(resp, post.content)
        posts.sort(key=lambda x: x.created_on, reverse=True)
        self.assertQuerysetEqual(posts, resp.context['post_list'])

    def test_post_index_paginates_properly(self):
        posts = [Post(title=f'test_title_{i}', content=f'test_content_{i}', author=self.users[0].author) for i in range(30)]
        for i, post in enumerate(posts):
            post.save()
            post.created_on = timezone.now()-timedelta(days=i)
            post.save()

        resp = self.client.get(reverse('blog:author_detail', kwargs={'slug': self.users[0].author.slug}))
        for i in range(20):
            self.assertContains(resp, posts[i].title)
            self.assertContains(resp, posts[i].content)

        resp = self.client.get(reverse('blog:author_detail', kwargs={'slug': self.users[0].author.slug}), data={'page': 2})
        for i in range(20, len(posts)):
            self.assertContains(resp, posts[i].title)
            self.assertContains(resp, posts[i].content)

    def test_post_index_hides_posts_from_other_authors(self):
        posts = []
        for i in range(10):
          post = Post(title=f'test_title_{i}', content=f'test_content_{i}', author=self.users[i % len(self.users)].author)
          post.save()
          posts.append(post)

        resp = self.client.get(reverse('blog:author_detail', kwargs={'slug': self.users[0].author.slug}))
        for post in posts:
            if post.author == self.users[0].author:
                self.assertContains(resp, post.title)
                self.assertContains(resp, post.content)
            else:
                self.assertNotContains(resp, post.title)
                self.assertNotContains(resp, post.content)

class PostsDetailViewTest(TestCase):

    def setUp(self):
        self.user = User(username='test_user', password='test_pass')
        self.user.save()
        self.user.author.bio='test_bio'
        self.user.author.visible = True
        self.user.author.save()

    def test_post_detail_returns_not_found(self):
        resp = self.client.get(reverse('blog:post_detail', kwargs={'pk': 1}))
        self.assertEquals(resp.status_code, 404)

    def test_post_detail_returns_not_found_for_posts_by_invisible_authors(self):
        user = User(username=f'test', password=f'test')
        user.save()
        user.author.visible = False
        user.author.save()
        post = Post(title=f'test_title', content=f'test_content', author=user.author)
        post.save()

        resp = self.client.get(reverse('blog:post_detail', kwargs={'pk': post.pk}))
        self.assertEquals(resp.status_code, 404)

    def test_post_detail_responds_with_title_content_author_username_bio(self):
        post = Post(title=''.join([f't{i}' for i in range(100)]), content=''.join([f't{i}' for i in range(500)]), author=self.user.author)
        post.save()
        resp = self.client.get(reverse('blog:post_detail', kwargs={'pk': post.pk}))
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, post.title)
        self.assertContains(resp, post.content)
        self.assertContains(resp, post.author.bio)
        self.assertContains(resp, post.author.user.username)

    def test_post_detail_returns_top_5_comments(self):
        post = Post(title=''.join([f't{i}' for i in range(100)]), content=''.join([f't{i}' for i in range(500)]), author=self.user.author)
        post.save()
        comments = [
            post.comment_set.create(commenter=self.user, votes=100, text='comment_0'),
            post.comment_set.create(commenter=self.user, votes=10, text='comment_1'),
            post.comment_set.create(commenter=self.user, votes=1000, text='comment_2'),
            post.comment_set.create(commenter=self.user, votes=-100, text='comment_3'),
            post.comment_set.create(commenter=self.user, votes=-50, text='comment_4'),
            post.comment_set.create(commenter=self.user, votes=500, text='comment_5'),
        ]
        for comment in comments:
            comment.save()
        comments.sort(key=lambda x: x.votes, reverse=True)

        resp = self.client.get(reverse('blog:post_detail', kwargs={'pk': post.pk}))
        for i in range(5):
            self.assertContains(resp, comments[i].text)
        self.assertQuerysetEqual(resp.context['comments'], comments[:5])
        
class PostCommentsViewTest(TestCase):

    def setUp(self):
        self.user = User(username='test_user', password='test_pass')
        self.user.save()
        self.user.author.visible = True
        self.user.author.save()

    def test_post_comments_index_returns_not_found(self):
        resp = self.client.get(reverse('blog:post_comment_index', kwargs={'pk': 1}))
        self.assertEqual(resp.status_code, 404)

    def test_post_comments_index_returns_not_found_for_post_with_hidden_author(self):
        user = User(username='test_hidden_user', password='test_hidden_pass')
        user.save()
        user.author.visible = False
        user.author.save()
        post = Post(title=f'test_title', content=f'test_content', author=user.author)
        post.save()
        resp = self.client.get(reverse('blog:post_comment_index', kwargs={'pk': post.pk}))
        self.assertEqual(resp.status_code, 404)

    def test_post_comments_index_returns_posts_sorted_by_creation_date(self):
        post = Post(title=''.join([f't{i}' for i in range(100)]), content=''.join([f't{i}' for i in range(500)]), author=self.user.author)
        post.save()
        comments = []
        day_deltas = [10, -5, 11, 2, -100]
        for i in range(len(day_deltas)):
            comment = post.comment_set.create(commenter=self.user, votes=100, text=f'comment_{i}')
            comment.save()
            comment.created_on = timezone.now() - timedelta(days=day_deltas[i])
            comment.save()
            comments.append(comment)
        
        comments.sort(key=lambda x: x.created_on, reverse=True)

        resp = self.client.get(reverse('blog:post_comment_index', kwargs={'pk': post.pk}), data={'sort': 'recent'})
        for comment in comments:
            self.assertContains(resp, comment.text)
        self.assertQuerysetEqual(resp.context['comments'], comments)
    