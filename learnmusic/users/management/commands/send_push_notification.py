"""
Django management command to send push notifications to users.
"""
import json
import os
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from pywebpush import webpush, WebPushException

from learnmusic.users.models import PushNotificationSubscription

User = get_user_model()

class Command(BaseCommand):
    help = 'Send push notifications to users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Email of the user to send notification to. If not provided, sends to all users.'
        )
        parser.add_argument(
            '--message',
            type=str,
            required=True,
            help='Message to send in the notification'
        )
        parser.add_argument(
            '--title',
            type=str,
            default='Tootology Notification',
            help='Title of the notification'
        )
        parser.add_argument(
            '--url',
            type=str,
            default='/notes/learning/',
            help='URL to open when notification is clicked'
        )

    def handle(self, *args, **options):
        user_email = options.get('user')
        message = options.get('message')
        title = options.get('title')
        url = options.get('url')

        # Get VAPID keys from settings
        vapid_private_key = getattr(settings, 'VAPID_PRIVATE_KEY', None)
        vapid_admin_email = getattr(settings, 'VAPID_ADMIN_EMAIL', None)

        if not vapid_private_key or not vapid_admin_email:
            raise CommandError(
                'VAPID_PRIVATE_KEY and VAPID_ADMIN_EMAIL must be set in settings. '
                'Generate keys using the pywebpush library.'
            )

        # Prepare notification data
        notification_data = {
            'title': title,
            'body': message,
            'icon': '/static/favicon/android-chrome-192x192.png',
            'data': {
                'url': url
            }
        }

        # Get subscriptions
        if user_email:
            try:
                user = User.objects.get(email=user_email)
                subscriptions = PushNotificationSubscription.objects.filter(user=user)
                if not subscriptions.exists():
                    self.stdout.write(self.style.WARNING(f'No push subscriptions found for user {user_email}'))
                    return
            except User.DoesNotExist:
                raise CommandError(f'User with email {user_email} does not exist')
        else:
            subscriptions = PushNotificationSubscription.objects.all()
            if not subscriptions.exists():
                self.stdout.write(self.style.WARNING('No push subscriptions found'))
                return

        # Send notifications
        success_count = 0
        error_count = 0

        for subscription in subscriptions:
            subscription_data = {
                'endpoint': subscription.endpoint,
                'keys': {
                    'p256dh': subscription.p256dh,
                    'auth': subscription.auth
                }
            }

            try:
                webpush(
                    subscription_info=subscription_data,
                    data=json.dumps(notification_data),
                    vapid_private_key=vapid_private_key,
                    vapid_claims={
                        'sub': f'mailto:{vapid_admin_email}'
                    }
                )
                success_count += 1
            except WebPushException as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f'Error sending notification to {subscription.user.email}: {str(e)}'))
                # If subscription is expired or invalid, delete it
                if e.response and e.response.status_code in (404, 410):
                    subscription.delete()
                    self.stdout.write(self.style.WARNING(f'Deleted invalid subscription for {subscription.user.email}'))

        self.stdout.write(self.style.SUCCESS(
            f'Sent {success_count} notifications successfully. {error_count} errors.'
        ))
