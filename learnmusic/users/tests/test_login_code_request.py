import pytest
from django.utils import timezone
from datetime import timedelta

from learnmusic.users.models import LoginCodeRequest
from learnmusic.users.tests.factories import LoginCodeRequestFactory

pytestmark = pytest.mark.django_db


class TestLoginCodeRequest:
    def test_too_many_recent_true(self):
        """Test that too_many_recent returns True when there are too many recent requests."""
        # Create 5 recent LoginCodeRequest objects
        email = "test@example.com"
        ip = "127.0.0.1"

        for _ in range(5):
            LoginCodeRequestFactory(
                email=email,
                ip_address=ip,
                requested_at=timezone.now()
            )

        # Check that too_many_recent returns True
        assert LoginCodeRequest.too_many_recent(email, ip, limit=5, window_minutes=10) is True

    def test_too_many_recent_false(self):
        """Test that too_many_recent returns False when there are not too many recent requests."""
        # Create 4 recent LoginCodeRequest objects (less than the limit of 5)
        email = "test@example.com"
        ip = "127.0.0.1"

        for _ in range(4):
            LoginCodeRequestFactory(
                email=email,
                ip_address=ip,
                requested_at=timezone.now()
            )

        # Check that too_many_recent returns False
        assert LoginCodeRequest.too_many_recent(email, ip, limit=5, window_minutes=10) is False

    def test_too_many_recent_old_requests_ignored(self):
        """Test that too_many_recent ignores old requests."""
        # Create 5 old LoginCodeRequest objects
        email = "test@example.com"
        ip = "127.0.0.1"

        for _ in range(5):
            LoginCodeRequestFactory(
                email=email,
                ip_address=ip,
                requested_at=timezone.now() - timedelta(minutes=11)  # Older than the 10-minute window
            )

        # Check that too_many_recent returns False
        assert LoginCodeRequest.too_many_recent(email, ip, limit=5, window_minutes=10) is False

    def test_too_many_recent_different_email(self):
        """Test that too_many_recent only counts requests for the specified email."""
        # Create 5 recent LoginCodeRequest objects for a different email
        email1 = "test1@example.com"
        email2 = "test2@example.com"
        ip = "127.0.0.1"

        for _ in range(5):
            LoginCodeRequestFactory(
                email=email1,
                ip_address=ip,
                requested_at=timezone.now()
            )

        # Check that too_many_recent returns False for a different email
        assert LoginCodeRequest.too_many_recent(email2, ip, limit=5, window_minutes=10) is False

    def test_too_many_recent_different_ip(self):
        """Test that too_many_recent only counts requests for the specified IP."""
        # Create 5 recent LoginCodeRequest objects for a different IP
        email = "test@example.com"
        ip1 = "127.0.0.1"
        ip2 = "192.168.0.1"

        for _ in range(5):
            LoginCodeRequestFactory(
                email=email,
                ip_address=ip1,
                requested_at=timezone.now()
            )

        # Check that too_many_recent returns False for a different IP
        assert LoginCodeRequest.too_many_recent(email, ip2, limit=5, window_minutes=10) is False

    def test_too_many_recent_mixed_age(self):
        """Test that too_many_recent correctly handles a mix of recent and old requests."""
        # Create 3 recent and 3 old LoginCodeRequest objects
        email = "test@example.com"
        ip = "127.0.0.1"

        # Recent requests
        for _ in range(3):
            LoginCodeRequestFactory(
                email=email,
                ip_address=ip,
                requested_at=timezone.now()
            )

        # Old requests
        for _ in range(3):
            LoginCodeRequestFactory(
                email=email,
                ip_address=ip,
                requested_at=timezone.now() - timedelta(minutes=11)  # Older than the 10-minute window
            )

        # Check that too_many_recent returns False (3 recent < limit of 5)
        assert LoginCodeRequest.too_many_recent(email, ip, limit=5, window_minutes=10) is False

        # Add 2 more recent requests to exceed the limit
        for _ in range(2):
            LoginCodeRequestFactory(
                email=email,
                ip_address=ip,
                requested_at=timezone.now()
            )

        # Check that too_many_recent returns True (5 recent = limit of 5)
        assert LoginCodeRequest.too_many_recent(email, ip, limit=5, window_minutes=10) is True
