from django.apps import AppConfig
from django.db import connection
from .utils import create_notification_types

class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'

    def ready(self):
        from .models import NotificationType
        if NotificationType._meta.db_table in connection.introspection.table_names():
            # Create notification types only if the table exists in the database
            create_notification_types()