from django import template
from django.db.models import query
from math import floor
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
