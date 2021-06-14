Django blog is a somewhat simple medium clone with reddit style upvotes and downvotes (but not replies) and the ability to decide which users can create posts.

**Requirements**
```
django
pillow
markdown
```
This project also includes a custom notifications library that works independently of the blog app. It currently supports basic notifications and private messages although I plan to expand it in the future.

**Custom Commands**
```
python manage.py resetgroups
```
Resets the default mod and author groups to their defaults. Useful if the default permissions in those groups change.

```
python manage.py createtestdata
```
Generates test data based on images in '<MEDIA_ROOT>/blog_post_header_images'. Requires the `lorem-text` package.

```
python manage.py validatevotescache
```
Validates that the value in comment.votes matches the total of CommentVotes for every comment

**Custom Settings**
```
AUTHOR_DEFAULT
```
Boolean. Should new users be automatically granted author status. Note that this applies to all new users not just ones created by the signup form.