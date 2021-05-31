from django.db import models
from django.contrib.auth.models import Permission, User, Group
from django.db.models.signals import post_save, post_init, pre_save
from django.dispatch import receiver
from django.template.defaultfilters import slugify, truncatechars
from django.urls import reverse
from os.path import basename
from .util import create_group_if_not_exists

class Post(models.Model):
    
    title = models.CharField(max_length=255)
    header_image = models.ImageField(null=True, blank=True, upload_to='blog_post_header_images/')
    header_image_name = models.CharField(null=True, blank=True, max_length=header_image.max_length)
    content = models.TextField(max_length=50000)
    tags = models.ManyToManyField('Tag')
    author = models.ForeignKey('Author', on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_on']
        permissions = [
            ("create_own_post", "Can create a new post with themselves as the author"),
        ]

    @staticmethod
    def can_user_create(user):
        return (user.has_perm('blog.create_own_post') and user.author.visible)

    def get_absolute_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.pk})

    def has_been_edited(self):
        return (self.updated_on - self.created_on).total_seconds() > 60

    def can_user_edit(self, user):
        return self.author == user.author or user.has_perm('blog.edit_post')

    def can_user_delete(self, user):
        return self.author == user.author or user.has_perm('blog.delete_post')

    def tags_str(self):
        return ', '.join([tag.__str__() for tag in self.tags.all()])

    def get_header_image_file_name(self):
        if self.header_image_name and self.header_image:
            return basename(self.header_image_name)
        elif self.header_image:
            return basename(self.header_image.name)
        else:
            return None

    def __str__(self):
        return truncatechars(self.title, 100)

class Comment(models.Model):
    commenter = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    text = models.TextField(max_length=5000)
    votes = models.IntegerField(default=0)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        permissions = [
            ("delete_comments_on_own_post", "Can delete any comment left on a post they created"),
        ]

    def can_user_edit(self, user):
        return self.commenter == user or user.has_perm('blog.change_comment')

    def can_user_delete(self, user):
        return self.commenter == user or user.has_perm('blog.delete_comment') or self.post.author == user.author

    def __str__(self):
        return f'{self.commenter}: {truncatechars(self.text, 100)}'

class Author(models.Model):
    AUTHOR_PERMS = ['modify_own_author', 'create_own_post', 'delete_comments_on_own_post']
    MOD_PERMS = ['delete_comment', 'delete_post', 'change_author', 'delete_user']
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=False)
    slug = models.SlugField(unique=True)
    bio = models.TextField(max_length=500, null=True, blank=True)
    visible = models.BooleanField(default=False)

    class Meta:
        permissions = [
            ("modify_own_author", "Can change their own author settings and visibilty status"),
        ]

    def set_author(self, is_author):
        group = create_group_if_not_exists('author', Author.AUTHOR_PERMS)
        if is_author:
            self.user.groups.add(group)
        else:
            self.user.groups.remove(group)
        self.visible = is_author

    def set_moderator(self, is_moderator):
        create_group_if_not_exists('mod', Author.MOD_PERMS)
        if is_moderator:
            self.user.groups.add(Group.objects.get(name='mod'))
        else:
            self.user.groups.remove(Group.objects.get(name='mod'))

    def can_user_edit(self, user):
        return user.has_perm('blog.change_author') or (user == self.user and user.has_perm('blog.modify_own_author')) or user.is_staff

    def get_absolute_url(self):
        return reverse('blog:author_detail', kwargs={'slug': self.slug})

    @receiver(post_save, sender=User)
    def create_user_author(sender, instance, created, **kwargs):
        if created:
            instance.author = Author.objects.create(user=instance, slug=slugify(instance.username))

    @receiver(post_save, sender=User)
    def save_user_author(sender, instance, created, **kwargs):
        instance.author.save()

    def __str__(self):
        return self.user.username

class Tag(models.Model):
    slug = models.SlugField(unique=True, null=True, blank=True)
    name = models.CharField(max_length=50, unique=True)

    @receiver(pre_save, sender='blog.Tag')
    def save_tag(sender, instance, **kwargs):
        instance.slug = slugify(instance.name)

    def __str__(self):
        return self.name
        