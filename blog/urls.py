from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('posts/', views.PostsIndexView.as_view(), name='posts_index'),
    path('posts/<int:pk>/', views.PostsDetailView.as_view(), name='post_detail'),
]
