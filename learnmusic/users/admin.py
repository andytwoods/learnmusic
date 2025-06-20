from allauth.account.decorators import secure_admin_login
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.contrib import messages
from django.core.management import call_command
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.translation import gettext_lazy as _

from .forms import UserAdminChangeForm
from .forms import UserAdminCreationForm
from .models import User, LoginCodeRequest, PushNotificationSubscription

if settings.DJANGO_ADMIN_FORCE_ALLAUTH:
    # Force the `admin` sign in process to go through the `django-allauth` workflow:
    # https://docs.allauth.org/en/latest/common/admin.html#admin
    admin.autodiscover()
    admin.site.login = secure_admin_login(admin.site.login)  # type: ignore[method-assign]


@admin.register(LoginCodeRequest)
class LoginCodeRequestAdmin(admin.ModelAdmin):
    list_display = ('email', 'ip_address', 'requested_at')
    ordering = ('-requested_at',)


@admin.register(PushNotificationSubscription)
class PushNotificationSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'endpoint', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__email', 'endpoint')
    ordering = ('-created_at',)
    actions = ['send_push_notification']

    def get_actions(self, request):
        actions = super().get_actions(request)
        if request.user.is_superuser:
            actions['send_notification_to_all'] = (
                self.send_notification_to_all,
                'send_notification_to_all',
                "Send push notification to all users"
            )
        return actions

    def send_notification_to_all(self, request, queryset):
        """Admin action to send push notifications to all users with subscriptions."""
        # Redirect to the custom form view for sending to all users
        return HttpResponseRedirect("../send-notification-to-all/")

    def send_push_notification(self, request, queryset):
        """Admin action to send push notifications to selected subscriptions."""
        # Store selected subscription IDs in session for the next view
        request.session['selected_subscriptions'] = [str(sub.id) for sub in queryset]
        # Redirect to the custom form view
        return HttpResponseRedirect("../send-push-notification/")
    send_push_notification.short_description = "Send push notification to selected subscriptions"

    def send_push_notification_view(self, request):
        """Custom admin view to send push notifications to selected subscriptions."""
        # Get selected subscriptions from session
        selected_subscription_ids = request.session.get('selected_subscriptions', [])
        if not selected_subscription_ids:
            self.message_user(request, "No subscriptions selected for notification.", level=messages.ERROR)
            return HttpResponseRedirect("../")

        subscriptions = PushNotificationSubscription.objects.filter(id__in=selected_subscription_ids)
        if not subscriptions.exists():
            self.message_user(
                request,
                "No valid subscriptions found.",
                level=messages.WARNING
            )
            return HttpResponseRedirect("../")

        # Get unique users from subscriptions
        users = User.objects.filter(id__in=subscriptions.values_list('user_id', flat=True).distinct())

        # Handle form submission
        if request.method == 'POST':
            message = request.POST.get('message')
            title = request.POST.get('title', 'Tootology Notification')

            if not message:
                self.message_user(request, "Message is required.", level=messages.ERROR)
                return render(request, 'admin/send_push_notification.html', {
                    'users': users,
                    'title': 'Send Push Notification',
                    'opts': self.model._meta,
                })

            # Send notifications to each subscription
            success_count = 0
            for subscription in subscriptions:
                try:
                    call_command('send_push_notification', user=subscription.user.email, message=message, title=title)
                    success_count += 1
                except Exception as e:
                    self.message_user(
                        request,
                        f"Error sending notification to {subscription.user.email}: {str(e)}",
                        level=messages.ERROR
                    )

            if success_count > 0:
                self.message_user(
                    request,
                    f"Successfully sent notifications to {success_count} subscriptions.",
                    level=messages.SUCCESS
                )

            return HttpResponseRedirect("../")

        # Display the form
        return render(request, 'admin/send_push_notification.html', {
            'users': users,
            'title': 'Send Push Notification',
            'opts': self.model._meta,
        })

    def send_notification_to_all_view(self, request):
        """Custom admin view to send push notifications to all users with subscriptions."""
        # Get all users with push subscriptions
        users_with_subscriptions = User.objects.filter(
            push_subscriptions__isnull=False
        ).distinct()

        if not users_with_subscriptions.exists():
            self.message_user(
                request,
                "No users have push notification subscriptions.",
                level=messages.WARNING
            )
            return HttpResponseRedirect("../")

        # Handle form submission
        if request.method == 'POST':
            message = request.POST.get('message')
            title = request.POST.get('title', 'Tootology Notification')

            if not message:
                self.message_user(request, "Message is required.", level=messages.ERROR)
                return render(request, 'admin/send_push_notification.html', {
                    'users': users_with_subscriptions,
                    'title': 'Send Push Notification to All Users',
                    'opts': self.model._meta,
                    'is_all_users': True,
                })

            # Send notifications to all users with subscriptions
            success_count = 0
            for user in users_with_subscriptions:
                try:
                    call_command('send_push_notification', user=user.email, message=message, title=title)
                    success_count += 1
                except Exception as e:
                    self.message_user(
                        request,
                        f"Error sending notification to {user.email}: {str(e)}",
                        level=messages.ERROR
                    )

            if success_count > 0:
                self.message_user(
                    request,
                    f"Successfully sent notifications to {success_count} users.",
                    level=messages.SUCCESS
                )

            return HttpResponseRedirect("../")

        # Display the form
        return render(request, 'admin/send_push_notification.html', {
            'users': users_with_subscriptions,
            'title': 'Send Push Notification to All Users',
            'opts': self.model._meta,
            'is_all_users': True,
        })

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'send-push-notification/',
                self.admin_site.admin_view(self.send_push_notification_view),
                name='send-push-notification',
            ),
            path(
                'send-notification-to-all/',
                self.admin_site.admin_view(self.send_notification_to_all_view),
                name='send-notification-to-all',
            ),
        ]
        return custom_urls + urls


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("name",)}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    list_display = ["email", "name", "is_superuser"]
    search_fields = ["name"]
    ordering = ["id"]
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )
    actions = ['send_push_notification']

    def send_push_notification(self, request, queryset):
        """Admin action to send push notifications to selected users."""
        # Store selected user IDs in session for the next view
        request.session['selected_users'] = [str(user.id) for user in queryset]
        # Redirect to the custom form view
        return HttpResponseRedirect("../send-push-notification/")
    send_push_notification.short_description = "Send push notification to selected users"

    def send_push_notification_view(self, request):
        """Custom admin view to send push notifications."""
        # Get selected users from session
        selected_user_ids = request.session.get('selected_users', [])
        if not selected_user_ids:
            self.message_user(request, "No users selected for notification.", level=messages.ERROR)
            return HttpResponseRedirect("../")

        users = User.objects.filter(id__in=selected_user_ids)

        # Check if any users have push subscriptions
        users_with_subscriptions = []
        for user in users:
            if PushNotificationSubscription.objects.filter(user=user).exists():
                users_with_subscriptions.append(user)

        if not users_with_subscriptions:
            self.message_user(
                request,
                "None of the selected users have push notification subscriptions.",
                level=messages.WARNING
            )
            return HttpResponseRedirect("../")

        # Handle form submission
        if request.method == 'POST':
            message = request.POST.get('message')
            title = request.POST.get('title', 'Tootology Notification')

            if not message:
                self.message_user(request, "Message is required.", level=messages.ERROR)
                return render(request, 'admin/send_push_notification.html', {
                    'users': users_with_subscriptions,
                    'title': 'Send Push Notification',
                    'opts': self.model._meta,
                })

            # Send notifications to each user
            success_count = 0
            for user in users_with_subscriptions:
                try:
                    call_command('send_push_notification', user=user.email, message=message, title=title)
                    success_count += 1
                except Exception as e:
                    self.message_user(
                        request,
                        f"Error sending notification to {user.email}: {str(e)}",
                        level=messages.ERROR
                    )

            if success_count > 0:
                self.message_user(
                    request,
                    f"Successfully sent notifications to {success_count} users.",
                    level=messages.SUCCESS
                )

            return HttpResponseRedirect("../")

        # Display the form
        return render(request, 'admin/send_push_notification.html', {
            'users': users_with_subscriptions,
            'title': 'Send Push Notification',
            'opts': self.model._meta,
        })

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'send-push-notification/',
                self.admin_site.admin_view(self.send_push_notification_view),
                name='send-push-notification',
            ),
        ]
        return custom_urls + urls
