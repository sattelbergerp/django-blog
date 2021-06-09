from django.urls import path
from . import views

app_name='notifications'
urlpatterns = [
    path('', views.NotificationIndexView.as_view(), name='notification_index'),
    path('<int:pk>/delete', views.NotificationDeleteView.as_view(), name='notification_delete'),
    path('messages/<int:pk>/create', views.PrivateMessageCreateView.as_view(), name='privatemessage_create'),
    path('messages/<int:pk>', views.PrivateMessageUserIndexView.as_view(), name='privatemessage_user_index'),
    path('messages/system', views.PrivateMessageUserIndexView.as_view(), name='privatemessage_system_index'),
]
