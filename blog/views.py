from django.shortcuts import render
from django.views.generic import ListView, DetailView
from .models import Post
# Create your views here.

class PostsIndexView(ListView):
    model = Post

class PostsDetailView(DetailView):
    model = Post