from django.shortcuts import render
from django.urls import reverse
from .models import Notification
from django.views.generic import ListView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin

# Create your views here.

class NotificationIndexView(LoginRequiredMixin, ListView):
    paginate_by = 20
    template_name = 'blog/notification_index.html'

    def get(self, request):
        user = request.user
        resp = super().get(request).render()
        for notification in user.notification_set.all():
            if not notification.seen:
                notification.seen = True
                notification.save()
        return resp

    def get_queryset(self):
        user = self.request.user
        return user.notification_set.all()

class NotificationDeleteView(DeleteView):
    model = Notification

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['next'] = self.request.GET.get('next', None)
        return context

    def get_success_url(self, *args, **kwargs):
        next = self.request.POST.get('next', None)
        return next if next else reverse('notifications:notification_index')