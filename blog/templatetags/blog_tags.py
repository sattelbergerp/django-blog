from django import template

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