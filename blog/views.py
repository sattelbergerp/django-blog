from notifications.models import NotificationType
from django.db.models.expressions import Func
from django.http.response import HttpResponseRedirect, HttpResponse
from django.http import Http404
from django.template.defaultfilters import default
from django.urls.base import reverse
from blog.forms import AuthorSettingsForm, UserSettingsForm, PostForm
from django.shortcuts import get_object_or_404, render
from django.views.generic import ListView, DetailView, DeleteView, CreateView, UpdateView
from django.views import View
from .models import Post, Author, Comment, Tag
#from notifications.models import Notification
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.contrib.auth import login
from django.contrib.auth.models import Permission
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.template.defaultfilters import slugify
from PIL import Image
from django.core.files.base import ContentFile
from os.path import join, exists
from os import remove
from django.db.models import Count, F, Q
# Create your views here.

class PostIndexView(ListView):
    model = Post
    paginate_by = 20
    queryset = Post.objects.filter(author__visible=True)

class PostDetailView(View):
    def get(self, request, pk):
        post = get_object_or_404(Post, pk=pk, author__visible=True)
        query = post.comment_set.annotate(num_upvotes=Count('commentvote', filter=Q(commentvote__type='u')))
        query = query.annotate(num_downvotes=Count('commentvote', filter=Q(commentvote__type='d')))
        query = query.annotate(num_votes=F('num_upvotes') - F('num_downvotes'))
        comments = query.order_by('-num_votes')[:5]
        return render(request, 'blog/post_detail.html', {'post': post, 'comments': comments, 'comment_count': post.comment_set.count()})

class PostCommentIndexView(ListView):
    paginate_by = 20
    template_name = 'blog/post_comment_index.html'
    context_object_name = 'comments'

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        context['post'] = self.post
        context['sort_by'] = self.sort_by
        return context

    def get_queryset(self):
        self.post = get_object_or_404(Post, pk=self.kwargs['pk'], author__visible=True)
        self.sort_by = 'top'
        if 'sort' in self.request.GET:
            sort = self.request.GET['sort']
            if sort == 'recent':
                self.sort_by = 'recent'
                return self.post.comment_set.order_by('-created_on').all()
        query = self.post.comment_set.annotate(num_upvotes=Count('commentvote', filter=Q(commentvote__type='u')))
        query = query.annotate(num_downvotes=Count('commentvote', filter=Q(commentvote__type='d')))
        query = query.annotate(num_votes=F('num_upvotes') - F('num_downvotes'))
        return query.order_by('-num_votes')

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

#TODO Only check user_form.isvalid() if can_user_edit is true
@login_required
def user_edit_view(request, slug):
    
    author = get_object_or_404(Author, slug=slug)
    can_edit_user = request.user == author.user
    can_edit_author = author.can_user_edit(request.user)
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
    if (post and not post.can_user_edit(request.user)) or (not post and not Post.can_user_create(request.user)):
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

class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post

    def test_func(self):
        return self.get_object().can_user_delete(self.request.user)

    def get_success_url(self, *args, **kwargs):
        return reverse('blog:author_detail', kwargs={'slug': self.get_object().author.slug})

class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    fields = ['text']

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['post'] = get_object_or_404(Post, pk=self.kwargs['pk'])
        context['next'] = self.request.GET.get('next', None)
        return context

    def form_valid(self, form):
        post = get_object_or_404(Post, pk=self.kwargs['pk'])
        comment = Comment(post=post, commenter=self.request.user, text=form.cleaned_data['text'])
        comment.save()
        post.author.user.notification_set.create(content=comment, type=NotificationType.get(name='new_comment_on_post'))
        next = self.request.POST.get('next', None)
        return HttpResponseRedirect(next if next else '/')

class CommentEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Comment
    fields = ['text']

    def test_func(self):
        return self.get_object().can_user_edit(self.request.user)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['post'] = self.get_object().post
        context['next'] = self.request.GET.get('next', None)
        return context

    def form_valid(self, form):
        comment = self.get_object()
        comment.text=form.cleaned_data['text']
        comment.save()
        next = self.request.POST.get('next', None)
        return HttpResponseRedirect(next if next else '/')

class CommentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Comment

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['next'] = self.request.GET.get('next', None)
        return context

    def test_func(self):
        return self.get_object().can_user_delete(self.request.user)

    def get_success_url(self, *args, **kwargs):
        next = self.request.POST.get('next', None)
        return next if next else '/'

class UserDetailView(ListView):
    paginate_by = 20
    template_name = 'blog/user_detail.html'
    context_object_name = 'comments'

    def get_context_data(self, *args, **kwargs):
        context =  super().get_context_data(*args, **kwargs)
        context['profile_user'] = self.user
        return context

    def get_queryset(self):
        self.user = get_object_or_404(Author, slug=self.kwargs['slug']).user
        
        return self.user.comment_set.order_by('-created_on').all()

class TagIndexView(ListView):
    model = Tag
    paginate_by = 100

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['sort_by'] = self.sort_by
        return context

    def get_queryset(self):
        query = Tag.objects.all().annotate(num_posts=Count('post')).filter(num_posts__gt=0)
        self.sort_by = self.request.GET.get('sort')
        if self.sort_by == 'least_posts':
            return query.order_by('num_posts')
        elif self.sort_by == 'name':
            return query.order_by('name')
        else:
            self.sort_by = 'most_posts'
            return query.order_by('-num_posts')

class TagDetailView(ListView):
    paginate_by = 20
    template_name = 'blog/tag_detail.html'

    def get_queryset(self):
        self.tag = get_object_or_404(Tag.objects, slug=self.kwargs['slug'])
        return self.tag.post_set.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tag'] = self.tag
        return context

def comment_vote(request, pk):
    if request.method != 'POST':
        raise Http404()
    comment = get_object_or_404(Comment, pk=pk)
    if comment.commenter == request.user:
        raise PermissionDenied
    type = request.POST.get('type', None)
    next = request.POST.get('next', None)
    if type=='upvote':
        if comment.has_voted(request.user, 'u'):
            comment.commentvote_set.filter(user=request.user, type='u').delete()
        else:
            comment.commentvote_set.filter(user=request.user, type='d').delete()
            comment.commentvote_set.create(user=request.user, type='u')
    if type=='downvote':
        if comment.has_voted(request.user, 'd'):
            comment.commentvote_set.filter(user=request.user, type='d').delete()
        else:
            comment.commentvote_set.filter(user=request.user, type='u').delete()
            comment.commentvote_set.create(user=request.user, type='d')

    if next:
        return HttpResponseRedirect(next if next else '/')
    else:
        return HttpResponse('Voted Ok')
