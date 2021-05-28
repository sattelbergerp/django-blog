from django.http.response import HttpResponseRedirect
from django.template.defaultfilters import default
from django.urls.base import reverse
from blog.forms import AuthorSettingsForm, UserSettingsForm, PostForm
from django.shortcuts import get_object_or_404, render
from django.views.generic import ListView, DetailView
from django.views import View
from .models import Post, Author, Comment, Tag
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.contrib.auth import login
from django.contrib.auth.models import Permission
from django.template.defaultfilters import slugify
from PIL import Image
from django.core.files.base import ContentFile
from os.path import join, exists
from os import remove
# Create your views here.

class PostIndexView(ListView):
    model = Post
    paginate_by = 20
    queryset = Post.objects.filter(author__visible=True)

class PostDetailView(View):
    def get(self, request, pk):
        post = get_object_or_404(Post, pk=pk, author__visible=True)
        comments = post.comment_set.order_by('-votes')[:5]
        return render(request, 'blog/post_detail.html', {'post': post, 'comments': comments, 'comment_count': post.comment_set.count()})

class PostCommentIndexView(ListView):
    paginate_by = 20
    template_name = 'blog/post_comment_index.html'
    context_object_name = 'comments'

    def get_queryset(self):
        self.post = get_object_or_404(Post, pk=self.kwargs['pk'], author__visible=True)
        if 'sort' in self.request.GET:
            sort = self.request.GET['sort']
            if sort == 'recent':
                return self.post.comment_set.order_by('-created_on').all()
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
def user_edit_view(request, slug):
    
    author = get_object_or_404(Author, slug=slug)
    can_edit_user = request.user == author.user
    can_edit_author = request.user.has_perm('blog.change_author') or (request.user == author.user and request.user.has_perm('blog.modify_own_author')) or request.user.is_staff
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

                if 'author_enabled' in author_form.cleaned_data:
                    author.set_author(author_form.cleaned_data['author_enabled'])
                    
                if 'moderator' in author_form.cleaned_data and request.user.is_staff:
                    author.set_moderator(author_form.cleaned_data['moderator'])
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

@login_required
def post_edit_view(request, pk=None):
    post = get_object_or_404(Post, pk=pk, author__visible=True) if pk else None
    if (post and post.author != request.user.author) or (not post and (not request.user.has_perm('blog.create_own_post') or not request.user.author.visible)):
        raise PermissionDenied
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            if not post:
                post = Post(author=request.user.author)
            post.title = form.cleaned_data.get('title')
            post.content = form.cleaned_data.get('content')
            post.save()
            header_image = form.cleaned_data.get('header_image')
            if header_image:
                
                post.header_image_name = header_image.name
                with Image.open(header_image) as im:
                    post.header_image = join(Post.header_image.field.upload_to, f'header_image_post_{post.pk}.jpeg')
                    image = Image.new('RGB', (im.width, im.height))
                    image.putdata(im.getdata())
                    image.save(post.header_image.path)
                    post.save()
            elif form.cleaned_data.get('remove_header_image', False):
                if exists(post.header_image.path):
                    remove(post.header_image.path)
                post.header_image = None
                post.header_image_name = None
                post.save()

            for tag_name in form.cleaned_data.get('tags', '').lower().split(','):
                try:
                    tag = Tag.objects.get(slug=slugify(tag_name.strip()))
                except Tag.DoesNotExist:
                    tag = Tag()
                tag.name = tag_name.strip()
                tag.save()
                post.tags.add(tag)
            post.save()
            return HttpResponseRedirect(reverse('blog:post_detail', kwargs={'pk': post.pk}))
    else:
        form = PostForm(instance=post, initial={'tags': post.tags_str() if post else ''})
    return render(request, 'blog/post_edit.html', {'form': form, 'post': post})