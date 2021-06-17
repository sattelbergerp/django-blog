from datetime import timedelta
from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth.models import Permission, User, Group
from django.contrib.auth import authenticate
from .models import Author, Tag, Post, Comment
from django.db.utils import IntegrityError
from django.utils import timezone
from django.conf import settings
from os.path import join, exists, basename
from os import makedirs, copy_file_range, stat
from PIL import Image
from shutil import copyfile
from .util import user_in_group

TEST_RESOURCES_PATH = getattr(settings, 'TEST_RESOURCES_PATH', 'test_resources')
TEST_MEDIA_ROOT = join(settings.BASE_DIR, 'test_resources/test_uploads_dir/')
Image.MAX_IMAGE_PIXELS = None

#util functions
def create_user(username, password, author_visible=False, author_bio=None, perms = [], author=False, mod=False, staff=False, superuser=False):
    user = User(username=username)
    user.save()
    user.set_password(password)
    user.author.visible = author_visible
    if author_bio:
        user.author.bio = author_bio

    if author:
        user.author.set_author(True)
    
    if mod:
        user.author.set_moderator(True)
    user.author.save()
    for perm in perms:
        user.user_permissions.add(Permission.objects.get(codename=perm))
    
    user.is_superuser = superuser
    user.is_staff = staff
    user.save()
    return reload_user(user)

def create_post(author, title, content, header_image=None):
    if type(author) == User:
        author = author.author
    post = Post(author=author, title=title, content=content)
    if header_image:
        copyfile(join(TEST_RESOURCES_PATH, header_image), join(TEST_MEDIA_ROOT, join(Post.header_image.field.upload_to, header_image)))
        post.header_image = join(Post.header_image.field.upload_to, header_image)
        post.header_image_name = header_image
    post.save()
    return post

def create_comment(post, commenter, text, upvotes, downvotes):
    comment = post.comment_set.create(commenter=commenter, text=text, votes = upvotes - downvotes)
    for i in range(upvotes):
        comment.commentvote_set.create(type='u', user=commenter)
    for i in range(downvotes):
        comment.commentvote_set.create(type='d', user=commenter)
    return comment

def reload_user(user):
    return User.objects.get(pk=user.pk)

#Model tests
@override_settings(AUTHOR_DEFAULT=False)
class AuthorModelTest(TestCase):

    def setUp(self):
        self.user = create_user("test_user", "test_pass")

    def test_author_created_when_user_created(self):
       self.assertTrue(self.user.author)

    def test_author_created_hidden(self):
       self.assertFalse(self.user.author.visible)

    def test_author_generates_correct_slug(self):
       user = create_user("test#_$user_slug%$^&", "test_pass")
       self.assertEqual(user.author.slug, 'test_user_slug')

    def test_deleting_user_deletes_author(self):
       self.assertEqual(Author.objects.count(), 1)
       self.user.delete()
       self.assertEqual(Author.objects.count(), 0)

    def test_creating_author_without_user_fails(self):
        author = Author()
        self.assertRaises(IntegrityError, author.save)

    def test_author_set_author_false_when_already_false_does_nothing(self):
       self.assertFalse(self.user.groups.exists())
       self.user.author.set_author(False)
       self.assertFalse(self.user.groups.exists())

    def test_author_set_author_true_creates_author_group_with_correct_permissions(self):
       self.assertFalse(Group.objects.filter(name='author').exists())
       self.user.author.set_author(True)
       group = Group.objects.get(name='author')
       for perm in Author.AUTHOR_PERMS:
           self.user.has_perm(f'blog.{perm}')

    def test_author_set_author_true_puts_a_user_in_author_group_and_sets_author_page_visible(self):
        self.assertFalse(user_in_group(self.user, 'author'))
        self.user.author.set_author(True)
        self.assertTrue(user_in_group(self.user, 'author'))
        self.assertTrue(self.user.author.visible)

    def test_author_set_author_false_removes_user_from_author_group_and_sets_page_invisible(self):
        user_author = create_user("author_user", "author_pass", author=True)
        self.assertTrue(user_in_group(user_author, 'author'))
        user_author.author.set_author(False)
        self.assertFalse(user_in_group(user_author, 'author'))
        self.assertFalse(user_author.author.visible)

    def test_author_set_moderator_false_when_already_false_does_nothing(self):
       self.assertFalse(self.user.groups.exists())
       self.user.author.set_moderator(False)
       self.assertFalse(self.user.groups.exists())

    def test_author_set_moderator_true_creates_mod_group_with_correct_permissions(self):
       self.assertFalse(Group.objects.filter(name='mod').exists())
       self.user.author.set_moderator(True)
       group = Group.objects.get(name='mod')
       for perm in Author.MOD_PERMS:
           self.user.has_perm(f'blog.{perm}')

    def test_author_set_moderator_true_puts_a_user_in_mod_group(self):
        self.assertFalse(user_in_group(self.user, 'mod'))
        self.user.author.set_moderator(True)
        self.assertTrue(user_in_group(self.user, 'mod'))

    def test_author_set_moderator_false_removes_user_from_mod_group(self):
        user_mod = create_user("mod_user", "mod_pass", mod=True)
        self.assertTrue(user_in_group(user_mod, 'mod'))
        user_mod.author.set_moderator(False)
        self.assertFalse(user_in_group(user_mod, 'mod'))

class TagModelTest(TestCase):

    def test_tag_generates_correct_slug(self):
        tag = Tag(name='Test Tag!')
        tag.save()
        self.assertEqual(tag.slug, 'test-tag')

class PostModelTest(TestCase):

    def setUp(self):
        self.user = create_user('test_user', 'test_pass')

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
@override_settings(AUTHOR_DEFAULT=False)
class PostIndexViewTest(TestCase):

    def setUp(self):
        self.user = create_user('test_user', 'test_pass', author_visible=True)

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
          user = create_user(f'test_{i}', f'test_{i}', author_visible=(i % 2) == 0)
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
        post = Post(title=''.join([f'ti' for i in range(100)]), content=''.join([f'ti' for i in range(500)]), author=self.user.author)
        post.save()
        resp = self.client.get(reverse('blog:post_index'))
        self.assertEquals(resp.status_code, 200)
        self.assertNotContains(resp, post.title)
        self.assertNotContains(resp, post.content)

@override_settings(AUTHOR_DEFAULT=False)
class AuthorDetailViewTest(TestCase):

    def setUp(self):
        self.users = []
        for i in range(4):
            user = create_user(f'test_user_{i}', f'test_pass_{i}', author_visible=True, author_bio=f'test_bio_{i}')
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

@override_settings(AUTHOR_DEFAULT=False)
class PostDetailViewTest(TestCase):

    def setUp(self):
        self.user = create_user(username='test_user', password='test_pass', author_visible=True, author_bio='test_bio')

    def test_post_detail_returns_not_found(self):
        resp = self.client.get(reverse('blog:post_detail', kwargs={'pk': 1}))
        self.assertEquals(resp.status_code, 404)

    def test_post_detail_returns_not_found_for_posts_by_invisible_authors(self):
        user = create_user(f'test_hidden_user', f'test_hidden_pass')
        post = Post(title=f'test_title', content=f'test_content', author=user.author)
        post.save()

        resp = self.client.get(reverse('blog:post_detail', kwargs={'pk': post.pk}))
        self.assertEquals(resp.status_code, 404)

    def test_post_detail_responds_with_title_content_author_username_bio(self):
        post = Post(title=''.join([f'ti' for i in range(100)]), content=''.join([f'ti' for i in range(500)]), author=self.user.author)
        post.save()
        resp = self.client.get(reverse('blog:post_detail', kwargs={'pk': post.pk}))
        self.assertEquals(resp.status_code, 200)
        self.assertContains(resp, post.title)
        self.assertContains(resp, post.content)
        self.assertContains(resp, post.author.bio)
        self.assertContains(resp, post.author.user.username)

    def test_post_detail_returns_top_5_comments(self):
        post = Post(title=''.join([f'ti' for i in range(100)]), content=''.join([f'ti' for i in range(500)]), author=self.user.author)
        post.save()
        comments = [
            create_comment(post, self.user, 'comment_0', 100, 120),
            create_comment(post, self.user, 'comment_0', 100, 2),
            create_comment(post, self.user, 'comment_0', 8, 0),
            create_comment(post, self.user, 'comment_0', 1, 120),
            create_comment(post, self.user, 'comment_0', 5, 60),
            create_comment(post, self.user, 'comment_0', 400, 120),
            create_comment(post, self.user, 'comment_0', 40, 20),
            create_comment(post, self.user, 'comment_0', 120, 120),
            create_comment(post, self.user, 'comment_0', 110, 10),
            create_comment(post, self.user, 'comment_0', 106, 40),
        ]
        comments.sort(key=lambda x: x.votes, reverse=True)

        resp = self.client.get(reverse('blog:post_detail', kwargs={'pk': post.pk}))
        for i in range(5):
            self.assertContains(resp, comments[i].text)
        self.assertQuerysetEqual(resp.context['comments'], comments[:5])
        
@override_settings(AUTHOR_DEFAULT=False)
class PostCommentsViewTest(TestCase):

    def setUp(self):
        self.user = create_user('test_user', 'test_pass', author_visible=True)

    def test_post_comments_index_returns_not_found(self):
        resp = self.client.get(reverse('blog:post_comment_index', kwargs={'pk': 1}))
        self.assertEqual(resp.status_code, 404)

    def test_post_comments_index_returns_not_found_for_post_with_hidden_author(self):
        user = create_user('test_hidden_user', 'test_hidden_pass')
        post = Post(title=f'test_title', content=f'test_content', author=user.author)
        post.save()
        resp = self.client.get(reverse('blog:post_comment_index', kwargs={'pk': post.pk}))
        self.assertEqual(resp.status_code, 404)

    def test_post_comments_index_returns_posts_sorted_by_creation_date(self):
        post = Post(title=''.join([f'ti' for i in range(100)]), content=''.join([f'ti' for i in range(500)]), author=self.user.author)
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

@override_settings(AUTHOR_DEFAULT=False)
class UserEditViewTest(TestCase):
    
    def setUp(self):
        self.no_perms_user = create_user('no_perms_user', 'test_pass', author_bio='Old Bio')
        self.author_perms_user = create_user('author_perms_user', 'test_pass', perms=['modify_own_author'], author_bio='Old Bio')
        self.mod_perms_user = create_user('mod_perms_user', 'test_pass', perms=['change_author'], author_bio='Old Bio')
        self.staff_user = create_user('staff_user', 'test_pass', staff=True, author_bio='Old Bio')
        self.superuser = create_user('superuser', 'test_pass', staff=True, superuser=True, author_bio='Old Bio')

    def test_user_edit_page_doesnt_allow_users_without_author_perms_to_set_author_settings(self):
        post_data = {'bio': 'New Bio'}
        self.client.force_login(self.no_perms_user)
        resp = self.client.post(reverse('blog:user_edit', kwargs={'slug': self.no_perms_user.author.slug}), post_data)
        user = reload_user(self.no_perms_user)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(user.author.bio, 'Old Bio')
        self.assertEqual(user.author.visible, False)

    def test_user_edit_page_allows_users_with_author_perms_to_set_own_author_settings(self):
        post_data = {'bio': 'New Bio'}
        self.client.force_login(self.author_perms_user)
        resp = self.client.post(reverse('blog:user_edit', kwargs={'slug': self.author_perms_user.author.slug}), post_data)
        user = reload_user(self.author_perms_user)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(user.author.bio, 'New Bio')

    def test_user_edit_page_doesnt_all_users_with_author_perms_to_change_others_author_settings(self):
        post_data = {'bio': 'New Bio'}
        self.client.force_login(self.author_perms_user)
        resp = self.client.post(reverse('blog:user_edit', kwargs={'slug': self.no_perms_user.author.slug}), post_data)
        user = reload_user(self.no_perms_user)
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(user.author.bio, 'Old Bio')

    def test_user_edit_page_allows_mods_to_change_other_users_author_status(self):
        post_data = {'author_enabled': True}
        self.client.force_login(self.mod_perms_user)
        resp = self.client.post(reverse('blog:user_edit', kwargs={'slug': self.no_perms_user.author.slug}), post_data)
        user = reload_user(self.no_perms_user)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(user.author.visible, True)
        self.assertTrue(user_in_group(user, 'author'))

    def test_user_edit_page_allows_staff_to_change_other_users_mod_status(self):
        post_data = {'moderator': True}
        self.client.force_login(self.staff_user)
        resp = self.client.post(reverse('blog:user_edit', kwargs={'slug': self.no_perms_user.author.slug}), post_data)
        user = reload_user(self.no_perms_user)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(user_in_group(user, 'mod'))

    
    def util_try_changing_user_password_and_email(self, user, login_user, should_work, new_password = 'new_password', current_password='test_pass', new_email='new@test.test'):
        self.assertIsNotNone(authenticate(username=user.username, password=current_password), msg='Check current password matches')
        current_email = user.email
        post_data = {'email': new_email, 'current_password': current_password, 'password': new_password, 'confirm_password': new_password}
        self.client.force_login(login_user)
        resp = self.client.post(reverse('blog:user_edit', kwargs={'slug': user.author.slug}), post_data)
        user = reload_user(user)
        if should_work:
            self.assertEqual(resp.status_code, 200)
            self.assertIsNone(authenticate(username=user.username, password=current_password), 'Old password still works')
            self.assertIsNotNone(authenticate(username=user.username, password=new_password), 'New password doesn\'t work')
            self.assertEqual(user.email, new_email)
        else:
            self.assertIsNone(authenticate(username=user.username, password=new_password))
            self.assertNotEqual(user.email, new_email)

    @override_settings(ENFORCE_PASSWORD_VALIDATION=False)
    def test_user_edit_page_allows_any_user_to_change_their_own_password_and_email(self):
        self.util_try_changing_user_password_and_email(self.no_perms_user, self.no_perms_user, True)
        self.util_try_changing_user_password_and_email(self.author_perms_user, self.author_perms_user, True)
        self.util_try_changing_user_password_and_email(self.mod_perms_user, self.mod_perms_user, True)
        self.util_try_changing_user_password_and_email(self.staff_user, self.staff_user, True)
        self.util_try_changing_user_password_and_email(self.superuser, self.superuser, True)

    def test_user_edit_page_blocks_no_perms_users_from_changing_other_users_password_and_email(self):
        self.util_try_changing_user_password_and_email(self.author_perms_user, self.no_perms_user, False)

    def test_user_edit_page_blocks_author_perms_users_from_changing_other_users_password_and_email(self):
        self.util_try_changing_user_password_and_email(self.no_perms_user, self.author_perms_user, False)

    def test_user_edit_page_blocks_mod_perms_users_from_changing_other_users_password_and_email(self):
        self.util_try_changing_user_password_and_email(self.no_perms_user, self.mod_perms_user, False)

    def test_user_edit_page_blocks_staff_users_from_changing_other_users_password_and_email(self):
        self.util_try_changing_user_password_and_email(self.no_perms_user, self.staff_user, False)

    def test_user_edit_page_blocks_superusers_from_changing_other_users_password_and_email(self):
        self.util_try_changing_user_password_and_email(self.no_perms_user, self.superuser, False)

    @override_settings(ENFORCE_PASSWORD_VALIDATION=True)
    def test_user_edit_page_permits_valid_password(self):
        self.util_try_changing_user_password_and_email(self.no_perms_user, self.no_perms_user, True, new_password='abcdef8A&')

@override_settings(AUTHOR_DEFAULT=False)
class UserDeleteViewTest(TestCase):
    
    def setUp(self):
        self.no_perms_user = create_user('no_perms_user', 'test_pass', author_bio='Old Bio')
        self.other_no_perms_user = create_user('author_perms_user', 'test_pass', author_bio='Old Bio')
        self.mod_perms_user = create_user('mod_perms_user', 'test_pass', mod=True, author_bio='Old Bio')

    def test_user_delete_allows_a_user_to_delete_their_own_account(self):
        self.client.force_login(self.no_perms_user)
        resp = self.client.post(reverse('blog:user_delete', kwargs={'slug': self.no_perms_user.author.slug}))
        self.assertRaises(User.DoesNotExist, lambda: User.objects.get(pk=self.no_perms_user.id))

    def test_user_delete_allows_a_mod_to_delete_users_accounts(self):
        self.client.force_login(self.mod_perms_user)
        resp = self.client.post(reverse('blog:user_delete', kwargs={'slug': self.no_perms_user.author.slug}))
        self.assertRaises(User.DoesNotExist, lambda: User.objects.get(pk=self.no_perms_user.id))

    def test_user_delete_disallows_users_deleting_other_accounts(self):
        self.client.force_login(self.other_no_perms_user)
        resp = self.client.post(reverse('blog:user_delete', kwargs={'slug': self.no_perms_user.author.slug}))
        self.assertEqual(User.objects.filter(pk=self.no_perms_user.id).count(), 1, 'Account does not exist')

@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT, AUTHOR_DEFAULT=False, DISABLE_IMAGE_UPLOADS=False)
class PostCreateViewTest(TestCase):
    
    def setUp(self):
        self.hidden_blog_user = create_user('hidden_blog_user', 'test_pass', author_bio='Old Bio', perms=['modify_own_author', 'create_own_post'])
        self.no_perms_user = create_user('no_perms_user', 'test_pass', author_bio='Old Bio', author_visible=True)
        self.author_perms_user = create_user('author_perms_user', 'test_pass', perms=['modify_own_author', 'create_own_post'], author_bio='Old Bio', author_visible=True)
        self.mod_perms_user = create_user('mod_perms_user', 'test_pass', perms=['change_author'], author_bio='Old Bio', author_visible=True)
        self.staff_user = create_user('staff_user', 'test_pass', staff=True, author_bio='Old Bio', author_visible=True)
        self.superuser = create_user('superuser', 'test_pass', staff=True, superuser=True, author_bio='Old Bio', author_visible=True)

    def test_post_create_returns_access_denied_for_users_without_create_own_post_perm(self):
        post_data = {'title': 'Test title', 'content': 'test_content'}
        self.client.force_login(self.no_perms_user)
        resp = self.client.post(reverse('blog:post_create'), post_data)
        self.assertEqual(resp.status_code, 403)

    def test_post_create_returns_access_denied_for_users_with_hidden_blogs(self):
        post_data = {'title': 'Test title', 'content': 'test_content'}
        self.client.force_login(self.hidden_blog_user)
        resp = self.client.post(reverse('blog:post_create'), post_data)
        self.assertEqual(resp.status_code, 403)

    def test_post_create_creates_post_and_uploads_image_correctly_and_converts_to_jpeg(self):
        self.client.force_login(self.author_perms_user)
        with open(join(TEST_RESOURCES_PATH, 'test_image.png'), 'rb') as fp:
            post_data = {'title': 'Test title', 'content': 'test_content', 'header_image': fp}
            resp = self.client.post(reverse('blog:post_create'), post_data, follow=True)
            post = resp.context.get('post')
            self.assertIsNotNone(post)
            self.assertEqual(post.title, post_data['title'])
            self.assertEqual(post.content, post_data['content'])
            self.assertEqual(post.author.user, self.author_perms_user)
            self.assertTrue(exists(post.header_image.path), msg=f'File {post.header_image.path} does not exist')
            self.assertEqual(basename(post.header_image.name), f'header_image_post_{post.pk}.jpeg')
            self.assertEqual(post.header_image_name, 'test_image.png')
            with Image.open(join(TEST_RESOURCES_PATH, 'test_image.png')) as source:
                with Image.open(post.header_image.path) as uploaded:
                    self.assertEqual(source.width, uploaded.width)
                    self.assertEqual(source.height, uploaded.height)
                    self.assertEqual(source.format, 'PNG')
                    self.assertEqual(uploaded.format, 'JPEG')

    def test_post_create_strips_metadata_from_image(self):
        self.client.force_login(self.author_perms_user)
        with open(join(TEST_RESOURCES_PATH, 'image_with_exif.jpg'), 'rb') as fp:
            post_data = {'title': 'Test title', 'content': 'test_content', 'header_image': fp}
            resp = self.client.post(reverse('blog:post_create'), post_data, follow=True)
            post = resp.context.get('post')
            self.assertIsNotNone(post)

            with Image.open(join(TEST_RESOURCES_PATH, 'image_with_exif.jpg')) as image:
                self.assertNotEqual(len(image.getexif()), 0, msg='Source image has no exif data')

            with Image.open(post.header_image.path) as image:
                self.assertEqual(len(image.getexif()), 0, msg='Uploaded image has metadata')

    def test_post_create_fails_for_high_resolution_images(self):
        self.client.force_login(self.author_perms_user)
        with open(join(TEST_RESOURCES_PATH, 'compression_bomb.jpeg'), 'rb') as fp:
            post_data = {'title': 'Test title', 'content': 'test_content', 'header_image': fp}
            resp = self.client.post(reverse('blog:post_create'), post_data, follow=True)
            post = resp.context.get('post')
            self.assertIsNone(post)
            
@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT, AUTHOR_DEFAULT=False, DISABLE_IMAGE_UPLOADS=False)
class PostEditViewTest(TestCase):
    
    def setUp(self):
        self.hidden_blog_user = create_user('hidden_blog_user', 'test_pass', author_bio='Old Bio', perms=['modify_own_author', 'create_own_post'])
        self.no_perms_user = create_user('no_perms_user', 'test_pass', author_bio='Old Bio', author_visible=True)
        self.author_perms_user = create_user('author_perms_user', 'test_pass', perms=['modify_own_author', 'create_own_post'], author_bio='Old Bio', author_visible=True)
        self.mod_perms_user = create_user('mod_perms_user', 'test_pass', perms=['change_author'], author_bio='Old Bio', author_visible=True)
        self.staff_user = create_user('staff_user', 'test_pass', staff=True, author_bio='Old Bio', author_visible=True)
        self.superuser = create_user('superuser', 'test_pass', staff=True, superuser=True, author_bio='Old Bio', author_visible=True)
        self.post_with_header_image = create_post(self.no_perms_user, 'With Header Image', 'Has a header image', header_image='test_image.png')
        self.post_without_header_image = create_post(self.no_perms_user, 'Without Header Image', 'No header image')
        self.post_with_hidden_author = create_post(self.hidden_blog_user, 'Hidden', 'hidden author')

    def test_edit_post_returns_not_found_for_post_that_does_not_exist(self):
        self.client.force_login(self.no_perms_user)
        post_data = {'title': 'Test title', 'content': 'test_content'}
        resp = self.client.post(reverse('blog:post_edit', kwargs={'pk': 1000000}), post_data)
        self.assertEqual(resp.status_code, 404)

    def test_edit_post_returns_not_found_for_post_with_hidden_author(self):
        self.client.force_login(self.hidden_blog_user)
        post_data = {'title': 'Test title', 'content': 'test_content'}
        resp = self.client.post(reverse('blog:post_edit', kwargs={'pk': self.post_with_hidden_author.pk}), post_data)
        self.assertEqual(resp.status_code, 404)
        
    def test_edit_post_returns_access_denied_for_users_that_didnt_create_the_post(self):
        self.client.force_login(self.author_perms_user)
        post_data = {'title': 'Test title', 'content': 'test_content'}
        resp = self.client.post(reverse('blog:post_edit', kwargs={'pk': self.post_without_header_image.pk}), post_data)
        self.assertEqual(resp.status_code, 403)

    def test_post_edit_modifies_post_and_uploads_image_correctly_and_converts_to_jpeg(self):
        self.client.force_login(self.no_perms_user)
        with open(join(TEST_RESOURCES_PATH, 'test_image.png'), 'rb') as fp:
            post_data = {'title': 'Test title', 'content': 'test_content', 'header_image': fp}
            resp = self.client.post(reverse('blog:post_edit', kwargs={'pk': self.post_without_header_image.pk}), post_data)
            post = Post.objects.get(pk=self.post_without_header_image.pk)
            self.assertEqual(post.title, post_data['title'])
            self.assertEqual(post.content, post_data['content'])
            self.assertEqual(post.author.user, self.no_perms_user)
            self.assertTrue(exists(post.header_image.path), msg=f'File {post.header_image.path} does not exist')
            self.assertEqual(basename(post.header_image.name), f'header_image_post_{post.pk}.jpeg')
            self.assertEqual(post.header_image_name, 'test_image.png')
            with Image.open(join(TEST_RESOURCES_PATH, 'test_image.png')) as source:
                with Image.open(post.header_image.path) as uploaded:
                    self.assertEqual(source.width, uploaded.width)
                    self.assertEqual(source.height, uploaded.height)
                    self.assertEqual(source.format, 'PNG')
                    self.assertEqual(uploaded.format, 'JPEG')

    def test_post_edit_strips_metadata_from_image(self):
        self.client.force_login(self.no_perms_user)
        with open(join(TEST_RESOURCES_PATH, 'image_with_exif.jpg'), 'rb') as fp:
            post_data = {'title': 'Test title', 'content': 'test_content', 'header_image': fp}
            resp = self.client.post(reverse('blog:post_edit', kwargs={'pk': self.post_with_header_image.pk}), post_data)
            post = Post.objects.get(pk=self.post_with_header_image.pk)

            with Image.open(join(TEST_RESOURCES_PATH, 'image_with_exif.jpg')) as image:
                self.assertNotEqual(len(image.getexif()), 0, msg='Source image has no exif data')

            with Image.open(post.header_image.path) as image:
                self.assertEqual(len(image.getexif()), 0, msg='Uploaded image has metadata')

    def test_post_edit_fails_for_high_resolution_images(self):
        self.client.force_login(self.no_perms_user)
        original_header_image = self.post_with_header_image.header_image_name
        with open(join(TEST_RESOURCES_PATH, 'compression_bomb.jpeg'), 'rb') as fp:
            post_data = {'title': 'Test title', 'content': 'test_content', 'header_image': fp}
            resp = self.client.post(reverse('blog:post_edit', kwargs={'pk': self.post_with_header_image.pk}), post_data)
            post = Post.objects.get(pk=self.post_with_header_image.pk)
            self.assertEqual(post.header_image_name, original_header_image)

    #Deletes uploaded test data
    def test_post_edit_removes_header_images_from_post(self):
        self.client.force_login(self.no_perms_user)
        original_header_image_path = self.post_with_header_image.header_image.path
        self.assertTrue(exists(original_header_image_path))
        
        post_data = {'title': 'Test title', 'content': 'test_content', 'remove_header_image': True}
        resp = self.client.post(reverse('blog:post_edit', kwargs={'pk': self.post_with_header_image.pk}), post_data)
        post = Post.objects.get(pk=self.post_with_header_image.pk)
        self.assertFalse(post.header_image)
        self.assertFalse(exists(original_header_image_path), msg='Header image was not deleted')
            
class PostDeleteViewTest(TestCase):

    def setUp(self):
        self.no_perms_user = create_user('no_perms_user', 'test_pass', author_visible=True)
        self.other_no_perms_user = create_user('other_no_perms_user', 'test_pass', author_visible=True)
        self.author_perms_user = create_user('author_perms_user', 'test_pass', author=True, author_visible=True)
        self.mod_perms_user = create_user('mod_perms_user', 'test_pass', mod=True, author_visible=True)
        self.post = create_post(self.no_perms_user, 'post1', 'post1 author')

    def test_post_delete_removes_a_users_post_if_they_created_it(self):
        self.client.force_login(self.no_perms_user)
        resp = self.client.post(reverse('blog:post_delete', kwargs={'pk': self.post.pk}))
        self.assertRaises(Post.DoesNotExist, lambda: Post.objects.get(pk=self.post.pk))

    def test_post_delete_mods_can_remove_other_users_posts(self):
        self.client.force_login(self.mod_perms_user)
        resp = self.client.post(reverse('blog:post_delete', kwargs={'pk': self.post.pk}))
        self.assertRaises(Post.DoesNotExist, lambda: Post.objects.get(pk=self.post.pk))

    def test_post_delete_other_users_cant_remove_others_posts(self):
        self.client.force_login(self.other_no_perms_user)
        resp = self.client.post(reverse('blog:post_delete', kwargs={'pk': self.post.pk}))
        self.assertEqual(resp.status_code, 403)
        self.assertTrue(Post.objects.filter(pk=self.post.pk).exists())

    def returns_access_denied_if_no_user_is_logged_in(self):
        resp = self.client.post(reverse('blog:post_delete', kwargs={'pk': self.post.pk}))
        self.assertEqual(resp.status_code, 403)
        self.assertTrue(Post.objects.filter(pk=self.post.pk).exists())

class CommentCreateViewTest(TestCase):

    def setUp(self):
        self.no_perms_user = create_user('no_perms_user', 'test_pass', author_visible=True)
        self.author_perms_user = create_user('author_perms_user', 'test_pass', author=True, author_visible=True)
        self.mod_perms_user = create_user('mod_perms_user', 'test_pass', mod=True, author_visible=True)
        self.post = create_post(self.author_perms_user, 'post1', 'post1 author')
        self.post_other = create_post(self.author_perms_user, 'post2', 'post2 author')

    def test_comment_create_returns_not_found_for_post_that_does_not_exists(self):
        self.client.force_login(self.no_perms_user)
        resp = self.client.get(reverse('blog:comment_create', kwargs={'pk': 0}))
        self.assertEqual(resp.status_code, 404)

    def test_comment_create_creates_a_comment_with_zero_votes_the_logged_in_user_and_the_selected_post(self):
        self.client.force_login(self.no_perms_user)
        resp = self.client.post(reverse('blog:comment_create', kwargs={'pk': self.post.pk}), {'text': 'Comment text!'})
        self.assertEqual(resp.status_code, 302)
        comment = Comment.objects.all()[0]
        self.assertEqual(comment.text, 'Comment text!')
        self.assertEqual(comment.votes, 0)
        self.assertEqual(comment.commenter, self.no_perms_user)
        self.assertEqual(comment.post, self.post)

class CommentEditViewTest(TestCase):

    def setUp(self):
        self.no_perms_user = create_user('no_perms_user', 'test_pass', author_visible=True)
        self.author_perms_user = create_user('author_perms_user', 'test_pass', author=True, author_visible=True)
        self.edit_comment_user = create_user('mod_perms_user', 'test_pass', perms=['change_comment'], author_visible=True)
        self.post = create_post(self.author_perms_user, 'post1', 'post1 author')
        self.post_other = create_post(self.author_perms_user, 'post2', 'post2 author')
        self.comment = self.post.comment_set.create(text='original text', commenter=self.no_perms_user)

    def test_comment_edit_returns_not_found_for_comment_that_does_not_exists(self):
        self.client.force_login(self.no_perms_user)
        resp = self.client.get(reverse('blog:comment_edit', kwargs={'pk': 0}))
        self.assertEqual(resp.status_code, 404)

    def test_comment_edit_lets_users_edit_their_own_comments(self):
        self.client.force_login(self.no_perms_user)
        resp = self.client.post(reverse('blog:comment_edit', kwargs={'pk': self.comment.pk}), {'text': 'New text'})
        self.assertEqual(resp.status_code, 302)
        comment = Comment.objects.get(pk=self.comment.pk)
        self.assertEqual(comment.text, 'New text')

    def test_comment_edit_lets_users_with_perms_edit_other_users_comments(self):
        self.client.force_login(self.edit_comment_user)
        resp = self.client.post(reverse('blog:comment_edit', kwargs={'pk': self.comment.pk}), {'text': 'New text'})
        self.assertEqual(resp.status_code, 302)
        comment = Comment.objects.get(pk=self.comment.pk)
        self.assertEqual(comment.text, 'New text')

    def test_comment_edit_doesnt_let_users_without_perms_edit_others_comments(self):
        self.client.force_login(self.author_perms_user)
        resp = self.client.post(reverse('blog:comment_edit', kwargs={'pk': self.comment.pk}), {'text': 'New text'})
        self.assertEqual(resp.status_code, 403)
        comment = Comment.objects.get(pk=self.comment.pk)
        self.assertEqual(comment.text, 'original text')

class CommentDeleteViewTest(TestCase):

    def setUp(self):
        self.no_perms_user = create_user('no_perms_user', 'test_pass', author_visible=True)
        self.other_no_perms_user = create_user('other_no_perms_user', 'test_pass', author_visible=True)
        self.author_perms_user = create_user('author_perms_user', 'test_pass', author=True, author_visible=True)
        self.mod_user = create_user('mod_perms_user', 'test_pass', mod=True, author_visible=True)
        self.post = create_post(self.author_perms_user, 'post1', 'post1 author')
        self.post_other = create_post(self.mod_user, 'post2', 'post2 author')
        self.comment = self.post.comment_set.create(text='original text', commenter=self.no_perms_user)
        self.comment_other = self.post_other.comment_set.create(text='original text', commenter=self.mod_user)

    def test_comment_delete_returns_not_found_for_comment_that_does_not_exists(self):
        self.client.force_login(self.no_perms_user)
        resp = self.client.get(reverse('blog:comment_delete', kwargs={'pk': 0}))
        self.assertEqual(resp.status_code, 404)

    def test_comment_delete_lets_users_delete_their_own_comments(self):
        self.client.force_login(self.no_perms_user)
        resp = self.client.post(reverse('blog:comment_delete', kwargs={'pk': self.comment.pk}))
        self.assertFalse(Comment.objects.filter(pk=self.comment.pk).exists())

    def test_comment_delete_lets_authors_delete_comments_on_their_own_post(self):
        self.client.force_login(self.author_perms_user)
        resp = self.client.post(reverse('blog:comment_delete', kwargs={'pk': self.comment.pk}))
        self.assertFalse(Comment.objects.filter(pk=self.comment.pk).exists())

    def test_comment_delete_lets_mods_delete_comments(self):
        self.client.force_login(self.mod_user)
        resp = self.client.post(reverse('blog:comment_delete', kwargs={'pk': self.comment.pk}))
        self.assertFalse(Comment.objects.filter(pk=self.comment.pk).exists())

    def test_comment_doesnt_let_users_delete_other_comments(self):
        self.client.force_login(self.no_perms_user)
        resp = self.client.post(reverse('blog:comment_delete', kwargs={'pk': self.comment_other.pk}))
        self.assertTrue(Comment.objects.filter(pk=self.comment_other.pk).exists())

    def test_comment_doesnt_let_authors_delete_comments_on_other_posts(self):
        self.client.force_login(self.author_perms_user)
        resp = self.client.post(reverse('blog:comment_delete', kwargs={'pk': self.comment_other.pk}))
        self.assertTrue(Comment.objects.filter(pk=self.comment_other.pk).exists())

class UserDetailViewTest(TestCase):

    def setUp(self):
        self.user = create_user('test_user1', 'test_pass', author_visible=True)
        self.other_user = create_user('test_user2', 'test_pass', author_visible=True)

    def test_user_detail_returns_not_found(self):
        resp = self.client.get(reverse('blog:user_detail', kwargs={'slug': 'does-not-exist'}))
        self.assertEqual(resp.status_code, 404)

    def test_user_detail_returns_comments_sorted_by_creation_date(self):
        post = Post(title=''.join([f'ti' for i in range(100)]), content=''.join([f'ti' for i in range(500)]), author=self.user.author)
        post.save()
        comments = []
        day_deltas = [10, -5, 11, 2, -100]
        for i in range(len(day_deltas)):
            comment = post.comment_set.create(commenter=(self.user) if i%2 else self.other_user, votes=100, text=f'comment_{i}')
            comment.save()
            comment.created_on = timezone.now() - timedelta(days=day_deltas[i])
            comment.save()
            comments.append(comment)
        
        comments.sort(key=lambda x: x.created_on, reverse=True)

        resp = self.client.get(reverse('blog:user_detail', kwargs={'slug': self.user.author.slug}))
        for comment in comments:
            if comment.commenter == self.user:
                self.assertContains(resp, comment.text)
            else:
                self.assertNotContains(resp, comment.text)