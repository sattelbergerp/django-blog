from django import template
from django.db.models import query
from math import floor
from blog.models import Notification
from os.path import join

register = template.Library()

@register.simple_tag(takes_context=True)
def format_pages(context, num_entries):
    page_obj = context.get('page_obj', None)
    pages = []
    if page_obj:
        if page_obj.number - num_entries > 1:
            pages.append(1)
            pages.append('...')
        for i in range(page_obj.number-num_entries, page_obj.number+num_entries+1):
            if i >= 1 and i <= page_obj.paginator.num_pages:
                pages.append(i)
        if page_obj.number + num_entries < page_obj.paginator.num_pages:
            pages.append('...')
            pages.append(page_obj.paginator.num_pages)
    return pages

@register.simple_tag(takes_context=True)
def current_url(context, *args):
    params = context['request'].GET.copy()
    for i in range(floor(len(args)/2)):
        params[args[i]] = args[i+1] if len(args) > i+1 else ''
    query_str = '&'.join(f'{k}={v}' for k, v in params.items())
    return f"{context['request'].path}?{query_str}"

@register.tag
def inline_notification(parser, token):
    try:
        tag_name, object_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(f'{token.contents.split()[0]} requires one argument')
    return InlineNotificationNode(object_name)
    
class InlineNotificationNode(template.Node):
    def __init__(self, notification):
        self.notification = template.Variable(notification)

    def render(self, context):
        try:
            notification = self.notification.resolve(context)
            if not isinstance(notification, Notification):
                raise ValueError(f'Expected Notification got {type(object)}')
            content = notification.content
            content_class = notification.content_type.model_class()
            meta = getattr(content_class, '_meta', None)
            content_type_name = content_class.__name__.lower()
            notifcation_inline_template = getattr(meta, 'notifcation_inline_template', join(meta.app_label, f'{content_type_name}_notification_inline.html'))
            notifcation_inline_context_name = getattr(meta, 'notifcation_inline_context_name', content_type_name)
            new_context = {}
            new_context[notifcation_inline_context_name] = content
            new_context['notification'] = notification
            return template.loader.get_template(notifcation_inline_template).render(new_context, context.get('request'))
        except template.VariableDoesNotExist:
            return 'Variable not resolved'
