from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Tag, Post, Comment, Author

class AuthorInline(admin.StackedInline):
    model = Author
    fields = ['bio', 'visible']

class CommentInline(admin.TabularInline):
    model = Comment

class UserAdmin(BaseUserAdmin):
    inlines = BaseUserAdmin.inlines + [AuthorInline]

class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author']
    inlines = [CommentInline]
    
class TagAdmin(admin.ModelAdmin):
    fields = ['name']

# Register your models here.
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Tag, TagAdmin)
