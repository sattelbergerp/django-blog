from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('posts/', views.PostIndexView.as_view(), name='post_index'),
    path('posts/<int:pk>/', views.PostDetailView.as_view(), name='post_detail'),
    path('posts/create', views.post_edit_view, name='post_create'),
    path('posts/<int:pk>/edit', views.post_edit_view, name='post_edit'),
    path('posts/<int:pk>/delete', views.PostDeleteView.as_view(), name='post_delete'),
    path('posts/<int:pk>/comments', views.PostCommentIndexView.as_view(), name='post_comment_index'),
    path('posts/<int:pk>/comments/new', views.CommentCreateView.as_view(), name='comment_create'),
    path('comments/<int:pk>/edit', views.CommentEditView.as_view(), name='comment_edit'),
    path('comments/<int:pk>/delete', views.CommentDeleteView.as_view(), name='comment_delete'),
    path('author/<slug:slug>/', views.AuthorDetailView.as_view(), name='author_detail'),
    path('user/<slug:slug>/edit', views.user_edit_view, name='user_edit'),
    path('user/<slug:slug>/', views.UserDetailView.as_view(), name='user_detail'),
]
