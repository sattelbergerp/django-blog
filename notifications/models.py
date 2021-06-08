from django.db import models
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.fields import GenericForeignKey, ContentType

# Create your models here.

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content = GenericForeignKey()
    seen = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    type = models.ForeignKey('NotificationType', on_delete=models.CASCADE)

    class Meta:
        ordering = ['-created_on']

class NotificationType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    label = models.CharField(max_length=50)
    description = models.CharField(max_length=500)
    