from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_init, pre_save
from django.dispatch import receiver
from django.template.defaultfilters import slugify, truncatechars
from django.urls import reverse

class Post(models.Model):
    title = models.CharField(max_length=255)
    header_image = models.ImageField(null=True, blank=True, upload_to='blog_post_header_images/')
    content = models.TextField(max_length=50000)
    tags = models.ManyToManyField('Tag')
    author = models.ForeignKey('Author', on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.pk})

    def has_been_edited(self):
        return (self.updated_on - self.created_on).total_seconds() > 60

    def __str__(self):
        return self.title

class Comment(models.Model):
    commenter = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    text = models.TextField(max_length=5000)
    votes = models.IntegerField(default=0)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.commenter}: {truncatechars(self.text, 25)}'

class Author(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=False)
    slug = models.SlugField(unique=True)
    bio = models.TextField(max_length=500, null=True, blank=True)
    visible = models.BooleanField(default=False)

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
        