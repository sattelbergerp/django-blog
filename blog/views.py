from blog.forms import AuthorSettingsForm, UserSettingsForm
from django.shortcuts import get_object_or_404, render
from django.views.generic import ListView, DetailView
from django.views import View
from .models import Post, Author, Comment
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib.auth import login
from django.contrib.auth.models import Permission
# Create your views here.

class PostIndexView(ListView):
    model = Post
    paginate_by = 20

class PostDetailView(View):
    def get(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        comments = post.comment_set.order_by('-votes')[:5]
        return render(request, 'blog/post_detail.html', {'post': post, 'comments': comments, 'comment_count': post.comment_set.count()})

class PostCommentIndexView(ListView):
    paginate_by = 20
    template_name = 'blog/post_comment_index.html'
    context_object_name = 'comments'

    def get_queryset(self):
        self.post = get_object_or_404(Post, pk=self.kwargs['pk'])
        return self.post.comment_set.order_by('-votes').all()

class AuthorDetailView(ListView):
    paginate_by = 20
    template_name = 'blog/author_detail.html'

    def get_queryset(self):
        self.author = get_object_or_404(Author.objects.filter(visible=True), slug=self.kwargs['slug'])
        return self.author.post_set.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['author'] = self.author
        return context

@login_required
def user_edit(request, slug):
    author = get_object_or_404(Author, slug=slug)
    can_edit_user = request.user == author.user
    can_edit_author = request.user.has_perm('blog.change_author') or (request.user == author.user and request.user.has_perm('blog.modify_own_author'))
    saved = False
    if not can_edit_user and not can_edit_author:
        raise PermissionDenied
    if request.method == 'POST':
        user_form = UserSettingsForm(request.POST, user=author.user)
        author_form = AuthorSettingsForm(request.POST)
        if user_form.is_valid() and author_form.is_valid():
            saved = True
            password = user_form.cleaned_data.get('password')
            email = user_form.cleaned_data.get('email')
            if can_edit_user:
                author.user.email = email
                if password:
                    author.user.set_password(password)
            if can_edit_author:
                author.bio = author_form.cleaned_data.get('bio')
                author.visible = author_form.cleaned_data.get('author_enabled')

                if author_form.cleaned_data.get('author_enabled'):
                    author.user.user_permissions.add(Permission.objects.get(codename='modify_own_author'), Permission.objects.get(codename='create_own_post'))
                else:
                    author.user.user_permissions.remove(Permission.objects.get(codename='modify_own_author'), Permission.objects.get(codename='create_own_post'))
                
                if author_form.cleaned_data.get('moderator'):
                    author.user.user_permissions.add(Permission.objects.get(codename='change_author'))
                else:
                    author.user.user_permissions.remove(Permission.objects.get(codename='change_author'))
                author.save()
            author.user.save()
            
            if request.user == author.user:
                login(request, author.user) #Changing a users password logs them out
            
    else:
       user_form = UserSettingsForm(user=author.user, initial={'email': author.user.email})
       author_form = AuthorSettingsForm(instance=author, initial={'author_enabled': author.visible, 'moderator': author.user.has_perm('blog.edit_author')})

    context = {
        'user_form': user_form, 
        'author_form': author_form, 
        'author': author, 
        'saved': saved,
        'can_edit_author': can_edit_author,
        'can_edit_user': can_edit_user,
    }

    return render(request, 'blog/user_edit.html', context)
