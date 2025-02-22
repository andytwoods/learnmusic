import pytest

from learnmusic.users.models import User


@pytest.mark.django_db
def test_toggle_help(user: User):
    # Initially, help should be True
    assert user.help is True

    # Toggle help and check
    user.toggle_help()
    assert user.help is False

    # Toggle again and check
    user.toggle_help()
    assert user.help is True


def test_user_get_absolute_url(user: User):
    assert user.get_absolute_url() == f"/users/{user.pk}/"
