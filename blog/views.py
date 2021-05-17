from django.shortcuts import get_object_or_404, render
from django.views.generic import ListView, DetailView
from django.views import View
from .models import Post, Author
# Create your views here.

class PostIndexView(ListView):
    model = Post
    paginate_by = 20

class PostDetailView(View):
    def get(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        comments = post.comment_set.order_by('-votes')[:5]
        return render(request, 'blog/post_detail.html', {'post': post, 'comments': comments})

class AuthorDetailView(ListView):
    paginate_by = 20
    template_name = 'blog/author_detail.html'

    def get_queryset(self):
        self.author = get_object_or_404(Author, slug=self.kwargs['slug'])
        return self.author.post_set.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['author'] = self.author
        return context