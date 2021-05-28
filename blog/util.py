from django.contrib.auth.models import User, Group, Permission

#Note: permissions are only assigned on group creation
def create_group_if_not_exists(name, perms):
    try:
        group = Group.objects.get(name=name)
    except Group.DoesNotExist:
        group = Group(name = name)
        group.save()
        for perm in perms:
            group.permissions.add(Permission.objects.get(codename=perm))
        group.save()
    return group

def user_in_group(user, group_name):
    try:
        user.groups.get(name=group_name)
        return True
    except Group.DoesNotExist:
        return False