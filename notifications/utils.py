from django.apps import apps

def create_notification_types():
        for model in apps.get_models():
            from notifications.models import NotificationType
            model_notification_meta = getattr(model, 'NotificationsMeta', None)
            if model_notification_meta:
                model_notification_types = getattr(model_notification_meta, 'notifications', None)
                if model_notification_types:
                    for notification_type_parms in model_notification_types:
                        name = notification_type_parms[0]
                        label = notification_type_parms[1] if len(notification_type_parms) > 1 else name
                        description = notification_type_parms[2] if len(notification_type_parms) > 2 else label
                        
                        notification_type, created = NotificationType.objects.get_or_create(name=name)
                        if label != notification_type.label or description != notification_type.description:
                            notification_type.label = label
                            notification_type.description = description

                            notification_type.save()