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
    path('comments/<int:pk>/vote', views.comment_vote, name='comment_vote'),
    path('authors/<slug:slug>/', views.AuthorDetailView.as_view(), name='author_detail'),
    path('users/<slug:slug>/edit', views.user_edit_view, name='user_edit'),
    path('users/<slug:slug>/', views.UserDetailView.as_view(), name='user_detail'),
    #path('notifications/', views.NotificationIndexView.as_view(), name='notification_index'),
   # path('notifications/<int:pk>/delete', views.NotificationDeleteView.as_view(), name='notification_delete'),
    path('tags/', views.TagIndexView.as_view(), name='tag_index'),
    path('tags/<slug:slug>/', views.TagDetailView.as_view(), name='tag_detail'),
]
