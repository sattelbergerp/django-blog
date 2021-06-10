from notifications.models import PrivateMessage, Notification, NotificationType
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

# Create your tests here.
class PrivateMessageModelTests(TestCase):

    def setUp(self):
        self.sender = User.objects.create(username='sender_username', password='test')
        self.receiver = User.objects.create(username='reciver_username', password='test')
        self.user_message = PrivateMessage.objects.create(sender=self.sender, receiver=self.receiver, text='user_message_contents')
        self.system_message = PrivateMessage.objects.create(receiver=self.receiver, text='system_message_contents')

    def test_is_system_message_return_true_for_messages_without_a_sender(self):
        self.assertEqual(self.system_message.is_system_message(), True)

    def test_is_system_message_return_false_for_messages_with_a_sender(self):
        self.assertEqual(self.user_message.is_system_message(), False)

    def test_get_sender_name_returns_system_for_messages_without_a_sender(self):
        self.assertEqual(self.system_message.get_sender_name(), 'system')

    def test_get_sender_name_returns_senders_username_for_messages_with_a_sender(self):
        self.assertEqual(self.user_message.get_sender_name(), self.sender.username)

    def test_get_receiver_name_returns_receivers_username_for_messages_with_a_receiver(self):
        self.assertEqual(self.user_message.get_receiver_name(), self.receiver.username)

class NotificationIndexViewTests(TestCase):

    def setUp(self):
        self.notification_type_one = NotificationType.objects.create(name=f'notification_type_1')
        self.notification_type_two = NotificationType.objects.create(name=f'notification_type_2')
        self.sender = User.objects.create(username='sender_username', password='test')
        self.receiver = User.objects.create(username='reciver_username', password='test')
        self.messages = [PrivateMessage.objects.create(text=f'receiver_test_message_{i}', sender=self.sender, receiver=self.receiver) for i in range(5)]
        self.sender_messages = [PrivateMessage.objects.create(text=f'sender_test_message_{i}', sender=self.receiver, receiver=self.sender) for i in range(5)]
        self.notifications = [Notification.objects.create(content=message, user=self.receiver, type=NotificationType.get(name='private_message')) for message in self.messages]
        self.sender_notifications = [Notification.objects.create(content=message, user=self.sender, type=NotificationType.get(name='private_message')) for message in self.sender_messages]
        self.type_one_notifications = [Notification.objects.create(content=message, user=self.sender, type=self.notification_type_one) for message in self.sender_messages]
        self.type_two_notifications = [Notification.objects.create(content=message, user=self.sender, type=self.notification_type_two) for message in self.sender_messages]

    def test_notifications_index_returns_notifications_for_user(self):
        self.client.force_login(self.receiver)
        resp = self.client.get(reverse('notifications:notification_index'))
        
        for notification in self.notifications:
            self.assertIn(notification, resp.context['notification_list'])
        for notification in self.sender_notifications:
            self.assertNotIn(notification, resp.context['notification_list'])

        self.client.force_login(self.sender)
        resp = self.client.get(reverse('notifications:notification_index'))
        for notification in self.notifications:
            self.assertNotIn(notification, resp.context['notification_list'])
        for notification in self.sender_notifications:
            self.assertIn(notification, resp.context['notification_list'])

    def test_notification_index_filters_by_notification_type(self):
        self.client.force_login(self.sender)
        resp = self.client.get(reverse('notifications:notification_index'), data={'notification_type_1': 'on', 'notification_type_2': 'on'})
        
        for notification in self.type_one_notifications:
            self.assertIn(notification, resp.context['notification_list'])
        for notification in self.type_two_notifications:
            self.assertIn(notification, resp.context['notification_list'])
        for notification in self.sender_notifications:
            self.assertNotIn(notification, resp.context['notification_list'])

class NotificationDeleteViewTest(TestCase):

    def setUp(self):
        self.sender = User.objects.create(username='sender_username', password='test')
        self.receiver = User.objects.create(username='receiver_username', password='test')
        self.messages = [PrivateMessage.objects.create(text=f'receiver_test_message_{i}', sender=self.sender, receiver=self.receiver) for i in range(5)]
        self.notifications = [Notification.objects.create(content=message, user=self.receiver, type=NotificationType.get(name='private_message')) for message in self.messages]
     

    def test_notification_delete_view_disallows_other_users_from_deleting_users_notifications(self):
        self.client.force_login(self.sender)
        resp = self.client.post(reverse('notifications:notification_delete', kwargs={'pk':self.notifications[0].id}))
        self.assertTrue(Notification.objects.filter(id=self.notifications[0].id).exists())

    def test_notification_delete_view_allows_users_to_delete_their_own_notifications(self):
        self.client.force_login(self.receiver)
        resp = self.client.post(reverse('notifications:notification_delete', kwargs={'pk':self.notifications[0].id}))
        self.assertFalse(Notification.objects.filter(id=self.notifications[0].id).exists())

class PrivateMessageUserDetailViewTest(TestCase):

    def setUp(self):
        self.sender = User.objects.create(username='sender_username', password='test')
        self.other_sender = User.objects.create(username='other_sender_username', password='test')
        self.unrelated_user = User.objects.create(username='unrelated_user', password='test')
        self.receiver = User.objects.create(username='reciver_username', password='test')
        self.other_receiver = User.objects.create(username='other_reciver_username', password='test')
        self.messages = [PrivateMessage.objects.create(text=f'receiver_test_message_{i}', sender=self.sender, receiver=self.receiver) for i in range(3)]
        self.sender_messages = [PrivateMessage.objects.create(text=f'sender_test_message_{i}', sender=self.receiver, receiver=self.sender) for i in range(3)]
        self.other_sender_messages = [PrivateMessage.objects.create(text=f'other_sender_test_message_{i}', sender=self.other_receiver, receiver=self.other_sender) for i in range(3)]
        self.other_messages = [PrivateMessage.objects.create(text=f'other_receiver_test_message_{i}', sender=self.other_sender, receiver=self.other_receiver) for i in range(3)]
        self.system_messages = [PrivateMessage.objects.create(text=f'system_test_message_{i}', receiver=self.receiver) for i in range(3)]

    def test_private_message_user_detail_view_returns_only_messages_sent_between_a_user_and_the_target(self):
        self.client.force_login(self.receiver)
        resp = self.client.get(reverse('notifications:privatemessage_user_detail', kwargs={'pk': self.sender.id}))
        for message in self.messages:
            self.assertIn(message, resp.context['privatemessage_list'])
        for message in self.sender_messages:
            self.assertIn(message, resp.context['privatemessage_list'])

        for message in self.other_messages:
            self.assertNotIn(message, resp.context['privatemessage_list'])
        for message in self.other_sender_messages:
            self.assertNotIn(message, resp.context['privatemessage_list'])
        for message in self.system_messages:
            self.assertNotIn(message, resp.context['privatemessage_list'])

    def test_private_message_user_detail_view_returns_no_messages_for_unrelated_users(self):
        self.client.force_login(self.unrelated_user)
        resp = self.client.get(reverse('notifications:privatemessage_user_detail', kwargs={'pk': self.sender.id}))
        for message in self.messages:
            self.assertNotIn(message, resp.context['privatemessage_list'])
        for message in self.sender_messages:
            self.assertNotIn(message, resp.context['privatemessage_list'])

        for message in self.other_messages:
            self.assertNotIn(message, resp.context['privatemessage_list'])
        for message in self.other_sender_messages:
            self.assertNotIn(message, resp.context['privatemessage_list'])
        for message in self.system_messages:
            self.assertNotIn(message, resp.context['privatemessage_list'])

    def test_private_message_user_detail_view_returns_only_system_messages_when_target_is_system(self):
        self.client.force_login(self.receiver)
        resp = self.client.get(reverse('notifications:privatemessage_system_detail'))
        for message in self.messages:
            self.assertNotIn(message, resp.context['privatemessage_list'])
        for message in self.sender_messages:
            self.assertNotIn(message, resp.context['privatemessage_list'])

        for message in self.other_messages:
            self.assertNotIn(message, resp.context['privatemessage_list'])
        for message in self.other_sender_messages:
            self.assertNotIn(message, resp.context['privatemessage_list'])
        for message in self.system_messages:
            self.assertIn(message, resp.context['privatemessage_list'])

class PrivateMessageCreateViewTest(TestCase):

    def setUp(self):
        self.sender = User.objects.create(username='sender_username', password='test')
        self.receiver = User.objects.create(username='reciver_username', password='test')

    def test_create_private_message_creates_a_private_message(self):
        self.client.force_login(self.sender)
        post_data = {'text': 'new_privatemessage'}
        resp = self.client.post(reverse('notifications:privatemessage_create', kwargs={'pk': self.receiver.pk}), data=post_data)
        self.assertEqual(PrivateMessage.objects.count(), 1)
        message = PrivateMessage.objects.all()[0]
        self.assertEqual(message.text, 'new_privatemessage')
        self.assertEqual(message.sender, self.sender)
        self.assertEqual(message.receiver, self.receiver)

    def test_create_private_message_creates_generates_a_notification_for_the_reciever(self):
        self.client.force_login(self.sender)
        post_data = {'text': 'new_privatemessage'}
        resp = self.client.post(reverse('notifications:privatemessage_create', kwargs={'pk': self.receiver.pk}), data=post_data)
        message = PrivateMessage.objects.all()[0]
        self.assertEqual(Notification.objects.count(), 1)
        notification = Notification.objects.all()[0]
        self.assertEqual(notification.type.name, 'private_message')
        self.assertEqual(notification.content, message)
        
class PrivateMessageIndexViewTest(TestCase):
    
    def setUp(self):
        self.sender = User.objects.create(username='sender_username', password='test')
        self.sender_matching_username_search = User.objects.create(username='sender_user_keyword_username', password='test')
        self.receiver = User.objects.create(username='reciver_username', password='test')
        self.other_receiver = User.objects.create(username='other_reciver_username', password='test')
        self.messages = [PrivateMessage.objects.create(text=f'receiver_test_message_{i}', sender=self.sender, receiver=self.receiver) for i in range(3)]
        self.messages_matching_text_search = [PrivateMessage.objects.create(text=f'search_text_keyword_message_{i}', sender=self.sender, receiver=self.receiver) for i in range(3)]
        self.messages_matching_username_search = [PrivateMessage.objects.create(text=f'receiver_test_message_{i}', sender=self.sender_matching_username_search, receiver=self.receiver) for i in range(3)]
        self.sender_messages = [PrivateMessage.objects.create(text=f'sender_test_message_{i}', sender=self.receiver, receiver=self.sender) for i in range(3)]
        self.other_sender_messages = [PrivateMessage.objects.create(text=f'other_sender_test_message_{i}', sender=self.other_receiver, receiver=self.sender) for i in range(3)]
    
    def test_private_message_index_view_returns_users_recieved_messages(self):
        self.client.force_login(self.receiver)
        resp = self.client.get(reverse('notifications:privatemessage_index'))
        for message in self.messages:
            self.assertIn(message, resp.context['privatemessage_list'])
        for message in self.messages_matching_text_search:
            self.assertIn(message, resp.context['privatemessage_list'])
        for message in self.messages_matching_username_search :
            self.assertIn(message, resp.context['privatemessage_list'])

        for message in self.sender_messages:
            self.assertNotIn(message, resp.context['privatemessage_list'])
        for message in self.other_sender_messages:
            self.assertNotIn(message, resp.context['privatemessage_list'])

    def test_private_message_index_searches_by_message_text(self):
        self.client.force_login(self.receiver)
        resp = self.client.get(reverse('notifications:privatemessage_index'), data={'search': 'text_keyword'})
        for message in self.messages_matching_text_search:
            self.assertIn(message, resp.context['privatemessage_list'])

        for message in self.messages:
            self.assertNotIn(message, resp.context['privatemessage_list'])
        for message in self.messages_matching_username_search:
            self.assertNotIn(message, resp.context['privatemessage_list'])

    def test_private_message_index_searches_by_sender_username(self):
        self.client.force_login(self.receiver)
        resp = self.client.get(reverse('notifications:privatemessage_index'), data={'search': 'user_keyword'})
        for message in self.messages_matching_username_search:
            self.assertIn(message, resp.context['privatemessage_list'])

        for message in self.messages:
            self.assertNotIn(message, resp.context['privatemessage_list'])
        for message in self.messages_matching_text_search:
            self.assertNotIn(message, resp.context['privatemessage_list'])

class PrivateMessageDeleteViewTest(TestCase):

    def setUp(self):
        self.sender = User.objects.create(username='sender_username', password='test')
        self.receiver = User.objects.create(username='receiver_username', password='test')
        self.messages = [PrivateMessage.objects.create(text=f'receiver_test_message_{i}', sender=self.sender, receiver=self.receiver) for i in range(5)]

    def test_privatemessage_delete_view_disallows_other_users_from_deleting_users_privatemessages(self):
        self.client.force_login(self.receiver)
        resp = self.client.post(reverse('notifications:privatemessage_delete', kwargs={'pk':self.messages[0].id}))
        self.assertTrue(PrivateMessage.objects.filter(id=self.messages[0].id).exists())

    def test_privatemessage_delete_view_allows_users_to_delete_their_own_privatemessages(self):
        self.client.force_login(self.sender)
        resp = self.client.post(reverse('notifications:privatemessage_delete', kwargs={'pk':self.messages[0].id}))
        self.assertFalse(PrivateMessage.objects.filter(id=self.messages[0].id).exists())