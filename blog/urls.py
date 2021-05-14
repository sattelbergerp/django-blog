from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('posts', views.PostsIndexView.as_view(), name='posts_index'),
]