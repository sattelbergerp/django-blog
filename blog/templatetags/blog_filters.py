from django import template
from math import log
from blog import models

register = template.Library()

def compact_int(value):
    if type(value) is int:
        abs_value = value if value >= 0 else -value
        if abs_value < 10000:
            return value
        exp = int(log(abs_value) / log(1000))
        char = ' KMBTQ'[exp]
        return f'{value/1000**exp: .01f}{char}'.strip()
    return type(value)

def can(action):
    def can_do(user, object):
        # If the permission we are trying to check requires a static method (create) we can't just pass an instance of an object
        # Check if the object is an instance of a string (Django uses 'SafeString' not str so we cant just user type(object) == str)
        if isinstance(object, str): 
            object = getattr(models, object) # Get our model class from models, This only work for models in our app so its not a great solution
        #If no user is logged in django gives you an AnonymousUser class that does have any of the user properties if no user is logged in
        #This must be filtered out because calling any of the permission objects with it will cause a crash
        if not user.is_authenticated:
            return False
        method = getattr(object, f'can_user_{action}')
        if not method:
            raise ValueError(f'Method can_user_{action} not found on {type(object)}')
        return method(user)
    
    return can_do

def has_voted(type):
    def wrapper(comment, user):
        return comment.has_voted(user, type)
    return wrapper

register.filter('intcompact', compact_int)
register.filter('can_edit', can('edit'))
register.filter('can_delete', can('delete'))
register.filter('can_create', can('create'))
register.filter('upvoted', has_voted('u'))
register.filter('downvoted', has_voted('d'))