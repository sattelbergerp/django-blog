from django.urls import path
from . import views

app_name='notifications'
urlpatterns = [
    path('notifications/', views.NotificationIndexView.as_view(), name='notification_index'),
    path('notifications/<int:pk>/delete', views.NotificationDeleteView.as_view(), name='notification_delete'),
]
