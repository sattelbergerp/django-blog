from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_init, pre_save
from django.dispatch import receiver
from django.template.defaultfilters import slugify

class Post(models.Model):
    title = models.CharField(max_length=255)
    header_image = models.ImageField(null=True, blank=True, upload_to='blog_post_header_images/')
    content = models.TextField(max_length=50000)
    tags = models.ManyToManyField('Tag')
    author = models.ForeignKey('Author', on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

class Comment(models.Model):
    commenter = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField(max_length=5000)
    votes = models.IntegerField(default=0)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

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

class Tag(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=50, unique=True)

    @receiver(pre_save, sender='blog.Tag')
    def save_tag(sender, instance, **kwargs):
        instance.slug = slugify(instance.name)
        