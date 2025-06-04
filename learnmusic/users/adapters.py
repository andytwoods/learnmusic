from __future__ import annotations

import typing

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now

if typing.TYPE_CHECKING:
    from allauth.socialaccount.models import SocialLogin
    from django.http import HttpRequest

    from learnmusic.users.models import User

from learnmusic.users.models import LoginCodeRequest


class AccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request: HttpRequest) -> bool:
        return getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)

    def save_user(self, request, user, form, commit=True):
        """
        Saves a new user and sends a notification email to the admin.
        """
        user = super().save_user(request, user, form, commit)

        # Send notification email to admin
        if settings.ADMINS:
            admin_emails = [admin_email for _, admin_email in settings.ADMINS]
            send_mail(
                subject="New User Registration",
                message=f"A new user has registered on LearnMusic:\n\nEmail: {user.email}\nName: {user.name}",
                from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else None,
                recipient_list=admin_emails,
                fail_silently=True,
            )

        return user

    def send_login_code(self, request, user, **kwargs):
        email = user.email
        ip = request.META.get("REMOTE_ADDR", "")

        if LoginCodeRequest.too_many_recent(email, ip):
            raise ValidationError(_("Too many login code requests. Please try again later."))

        # Log this request
        LoginCodeRequest.objects.create(email=email, ip_address=ip, requested_at=now())

        # Call the default sending behaviour
        super().send_login_code(request, user, **kwargs)


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(
        self,
        request: HttpRequest,
        sociallogin: SocialLogin,
    ) -> bool:
        return getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)

    def populate_user(
        self,
        request: HttpRequest,
        sociallogin: SocialLogin,
        data: dict[str, typing.Any],
    ) -> User:
        """
        Populates user information from social provider info.

        See: https://docs.allauth.org/en/latest/socialaccount/advanced.html#creating-and-populating-user-instances
        """
        user = super().populate_user(request, sociallogin, data)
        if not user.name:
            if name := data.get("name"):
                user.name = name
            elif first_name := data.get("first_name"):
                user.name = first_name
                if last_name := data.get("last_name"):
                    user.name += f" {last_name}"
        return user

    def save_user(self, request, sociallogin, form=None):
        """
        Saves a newly signed-up social login and sends a notification email to the admin.
        """
        user = super().save_user(request, sociallogin, form)

        # Send notification email to admin
        if settings.ADMINS:
            admin_emails = [admin_email for _, admin_email in settings.ADMINS]
            provider = sociallogin.account.provider.capitalize()
            send_mail(
                subject=f"New {provider} Social Login",
                message=f"A new user has registered on LearnMusic using {provider}:\n\nEmail: {user.email}\nName: {user.name}",
                from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else None,
                recipient_list=admin_emails,
                fail_silently=True,
            )

        return user
