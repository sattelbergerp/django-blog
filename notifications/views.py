from django.dispatch.dispatcher import receiver
from django.shortcuts import render
from django.urls import reverse
from django.views.generic.edit import CreateView
from .models import Notification, NotificationType, PrivateMessage
from django.views.generic import ListView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.db.models import Q

# Create your views here.

class NotificationIndexView(LoginRequiredMixin, ListView):
    paginate_by = 20
    template_name = 'blog/notification_index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["notificationtype_list"] = self.notificationtypes
        context["included_notificationtypes"] = self.included_notificationtypes

        return context
    

    def get(self, request):
        self.user = request.user
        self.notificationtypes = NotificationType.objects.all()
        self.included_notificationtypes = []
        for notificationtype in self.notificationtypes:
            if notificationtype.name in request.GET and request.GET[notificationtype.name].lower() == 'on':
                self.included_notificationtypes.append(notificationtype)
                
        resp = super().get(request).render()
        for notification in self.user.notification_set.all():
            if not notification.seen:
                notification.seen = True
                notification.save()
        return resp

    def get_queryset(self):
        user = self.request.user
        query = user.notification_set.all()
        if len(self.included_notificationtypes) > 0:
            query = query.filter(type__in=self.included_notificationtypes)
        return query

class NotificationDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Notification

    def test_func(self):
        return self.request.user == self.get_object().user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['next'] = self.request.GET.get('next', None)
        return context

    def get_success_url(self, *args, **kwargs):
        next = self.request.POST.get('next', None)
        return next if next else reverse('notifications:notification_index')

class PrivateMessageCreateView(LoginRequiredMixin, CreateView):
    model = PrivateMessage
    fields = ['text']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile_user"] = get_object_or_404(User, pk=self.kwargs['pk'])
        return context
    

    def form_valid(self, form):
        user = get_object_or_404(User, pk=self.kwargs['pk'])
        message = PrivateMessage(sender=self.request.user, receiver=user, text=form.cleaned_data['text'])
        message.save()
        user.notification_set.create(content=message, type=NotificationType.get('private_message'))
        #user.notification_set.create(content=message)
        
        return HttpResponseRedirect(reverse('notifications:privatemessage_user_index', kwargs={'pk':user.id}))

class PrivateMessageUserIndexView(LoginRequiredMixin, ListView):
    model = PrivateMessage
    template_name = 'notifications/privatemessage_user_list.html'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile_user"] = self.target
        return context
    

    def get_queryset(self):
        self.user = self.request.user
        self.target = None
        if 'pk' in self.kwargs:
            self.target = get_object_or_404(User, pk=self.kwargs['pk'])
        
        if self.target:
            return PrivateMessage.objects.filter((Q(sender=self.user) and Q(receiver=self.target)) | (Q(sender=self.target) and Q(receiver=self.user))).filter(Q(sender__isnull=False))
        else:
            return PrivateMessage.objects.filter((Q(receiver=self.user) and Q(sender__isnull=True)))