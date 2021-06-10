from django.db import models
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.fields import GenericForeignKey, ContentType
from .utils import create_notification_types
from django.db.models.deletion import CASCADE
from django.urls import reverse
from django.db.models.signals import pre_delete
from django.dispatch import receiver

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

    def __str__(self):
        return str(self.content)
    
    @receiver(pre_delete)
    def my_callback(sender, instance, **kwargs):
        instance_type = ContentType.objects.get(app_label=instance._meta.app_label, model=type(instance).__name__.lower())
        try:
            target = Notification.objects.get(object_id=instance.pk, content_type_id=instance_type.pk)
            target.delete()
        except Notification.DoesNotExist:
            pass

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

    def __str__(self):
        return f'label'

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

    def get_sender_messages_url(self):
        if self.is_system_message():
            return reverse('notifications:privatemessage_system_detail')
        else:
            return reverse('notifications:privatemessage_user_detail', kwargs={'pk': self.sender.id})

    def get_receiver_messages_url(self):
        return reverse('notifications:privatemessage_user_detail', kwargs={'pk': self.receiver.id})

    def __str__(self):
        return f'{self.text}'

    