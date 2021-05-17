from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('posts/', views.PostIndexView.as_view(), name='post_index'),
    path('posts/<int:pk>/', views.PostDetailView.as_view(), name='post_detail'),
]
