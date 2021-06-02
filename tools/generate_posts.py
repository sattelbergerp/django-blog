import os
import sys
import inspect

sys.path.insert(1, os.path.join(sys.path[0], '..')) #Set python to resolve imports from parent directory (project root)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "blog_project.settings")
import django
django.setup()
from blog.models import Post, Comment, Author, Tag
from django.contrib.auth.models import User
from lorem_text import lorem
from random import randrange
from math import floor

MEDIA_TARGET = 'media'
POSTS_IMAGE_TARGET = 'blog_post_header_images'

users = []
for i in range(2000):
    username=f'test_user_{i}'
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        user = User(username=username, password= f'test_pass_{i}')
    finally:
        user.save()
        users.append(user)

authors = []
for i in range(25):
    username=f'test_author_{i}'
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        user = User(username=username, password= f'test_author_pass_{i}')
    finally:
        user.save()
        user.author.bio = lorem.paragraph()
        user.author.visible = True
        user.author.save()
        authors.append(user)
        users.append(user)

tags = []
for i in range(1000):
    tag_name=f'test_tag_{i}'
    try:
        tag = Tag.objects.get(name=tag_name)
    except Tag.DoesNotExist:
        tag = Tag(name=tag_name)
    finally:
        tag.save()
        tags.append(tag)

files = os.listdir(os.path.join(MEDIA_TARGET, POSTS_IMAGE_TARGET))
print('Generating posts...',end='')

for i, file in enumerate(files):
    print(f'\rGenerating posts... ({i+1}/{len(files)})',end='')
    file_path = os.path.join(POSTS_IMAGE_TARGET, file)
    post_set = Post.objects.filter(header_image=file_path)
    if post_set.count() < 1:
        post = Post(title=lorem.sentence(), content=lorem.paragraphs(5), header_image=file_path, author=authors[randrange(0, len(authors)-1)].author)
        post.save()
    else:
        post = post_set[0]

    if post.tags.all().count() == 0:
        for tag in tags:
            if randrange(0, 25) == 0:
                post.tags.add(tag)
    
    if post.tags.all().count() == 0:
        for tag in tags:
            if randrange(0, 4) == 0:
                post.tags.add(tag)
    
    if post.comment_set.all().count() == 0:
        tc = randrange(10, 50)
        for j in range(tc):
            comment = Comment(post=post, commenter=users[randrange(0, len(users)-1)], text=lorem.paragraph())
            comment.save()
            total = randrange(0, 2000)
            p, lp = 0, -1
            for k in range(total):
                p = floor(100.0/(total*tc)*(k+(total*j)))
                if p != lp:
                    print(f'\rGenerating posts... ({i+1}/{len(files)}) {p}%',end='')
                    lp = p
                comment.commentvote_set.create(user=users[randrange(0, len(users)-1)], type='u' if randrange(0,2)==0 else 'd')


