from django.db import models
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.fields import GenericForeignKey, ContentType
from .utils import create_notification_types
from django.db.models.deletion import CASCADE

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

    def get(name):
        try:
            return NotificationType.objects.get(name=name)
        except NotificationType.DoesNotExist:
            create_notification_types()
            return NotificationType.objects.get(name=name)

class PrivateMessage(models.Model):
    sender = models.ForeignKey(User, blank=True, null=True, on_delete=CASCADE, related_name='user_sender')
    receiver = models.ForeignKey(User, on_delete=CASCADE, related_name='user_reciever')
    text = models.TextField(max_length=500)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_on']

    class NotificationsMeta:
        notifications = [
            ('private_message', 'Private message recieved', 'When a user send you a private messsage')
        ]

    def is_system_message(self):
        return self.sender == None

    def get_sender_name(self):
        if self.is_system_message():
            return 'system'
        return self.sender.username

    def get_receiver_name(self):
        return self.receiver.username

    