from django.urls import path
from . import views

app_name='notifications'
urlpatterns = [
    path('', views.NotificationIndexView.as_view(), name='notification_index'),
    path('<int:pk>/delete', views.NotificationDeleteView.as_view(), name='notification_delete'),
    path('messages/', views.PrivateMessageIndexView.as_view(), name='privatemessage_index'),
    path('messages/<int:pk>', views.PrivateMessageUserDetailView.as_view(), name='privatemessage_user_detail'),
    path('messages/system', views.PrivateMessageUserDetailView.as_view(), name='privatemessage_system_detail'),
    path('messages/<int:pk>/create', views.PrivateMessageCreateView.as_view(), name='privatemessage_create'),
    path('messages/<int:pk>/delete', views.PrivateMessageDeleteView.as_view(), name='privatemessage_delete'),
]
