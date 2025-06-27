
from typing import ClassVar
from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import CharField, BooleanField, EmailField, GenericIPAddressField, DateTimeField, Model, OneToOneField, CASCADE, TimeField, TextField, ForeignKey
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .managers import UserManager


class LoginCodeRequest(Model):
    email = EmailField()
    ip_address = GenericIPAddressField()
    requested_at = DateTimeField(default=timezone.now)

    @classmethod
    def too_many_recent(cls, email, ip, limit=5, window_minutes=10):
        cutoff = timezone.now() - timedelta(minutes=window_minutes)
        return cls.objects.filter(
            email=email,
            ip_address=ip,
            requested_at__gte=cutoff,
        ).count() >= limit


class User(AbstractUser):
    """
    Default custom user model for LearnMusic.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    # First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]
    email = EmailField(_("email address"), unique=True)
    username = None  # type: ignore[assignment]
    pushover_key = models.CharField(max_length=255, blank=True)
    timezone = CharField(max_length=50, default="UTC", help_text="User's timezone for reminders")


    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects: ClassVar[UserManager] = UserManager()

    def get_absolute_url(self) -> str:
        return reverse("users:detail", kwargs={"pk": self.id})





