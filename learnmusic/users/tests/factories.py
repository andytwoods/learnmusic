from collections.abc import Sequence
from typing import Any

from factory import Faker
from factory import post_generation
from factory.django import DjangoModelFactory

from learnmusic.users.models import User, LoginCodeRequest


class UserFactory(DjangoModelFactory[User]):
    email = Faker("email")
    name = Faker("name")

    @post_generation
    def password(self, create: bool, extracted: Sequence[Any], **kwargs):  # noqa: FBT001
        password = (
            extracted
            if extracted
            else Faker(
                "password",
                length=42,
                special_chars=True,
                digits=True,
                upper_case=True,
                lower_case=True,
            ).evaluate(None, None, extra={"locale": None})
        )
        self.set_password(password)
        if create:
            # Explicitly save the instance to avoid relying on deprecated postgeneration auto-save
            self.save()

    class Meta:
        model = User
        django_get_or_create = ["email"]
        skip_postgeneration_save = True


class LoginCodeRequestFactory(DjangoModelFactory):
    email = Faker("email")
    ip_address = "127.0.0.1"
    requested_at = Faker("date_time", tzinfo=None)

    class Meta:
        model = LoginCodeRequest
