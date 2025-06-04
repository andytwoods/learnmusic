import pytest
from django.core.exceptions import ValidationError
from django.test import RequestFactory
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock

from learnmusic.users.adapters import AccountAdapter, SocialAccountAdapter
from learnmusic.users.models import LoginCodeRequest, User
from learnmusic.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class MockAccountAdapter(AccountAdapter):
    """A mock adapter that overrides the parent's send_login_code method to avoid sending emails."""

    def __init__(self):
        super().__init__()
        self.parent_called = False

    def send_login_code(self, request, user, **kwargs):
        """Override the parent's send_login_code method to avoid sending emails."""
        email = user.email
        ip = request.META.get("REMOTE_ADDR", "")

        if LoginCodeRequest.too_many_recent(email, ip):
            raise ValidationError("Too many login code requests. Please try again later.")

        # Log this request
        LoginCodeRequest.objects.create(email=email, ip_address=ip, requested_at=timezone.now())

        # Mark that the parent method would have been called
        self.parent_called = True


class TestAccountAdapter:
    def test_send_login_code_success(self, rf: RequestFactory):
        """Test that send_login_code works correctly when rate limit is not exceeded."""
        # Create a user
        user = UserFactory()

        # Create a request
        request = rf.get("/fake-url/")
        request.META["REMOTE_ADDR"] = "127.0.0.1"

        # Create a mock adapter
        adapter = MockAccountAdapter()

        # Call the method
        adapter.send_login_code(request, user)

        # Check that a LoginCodeRequest was created
        assert LoginCodeRequest.objects.filter(email=user.email, ip_address="127.0.0.1").exists()

        # Check that the parent method would have been called
        assert adapter.parent_called is True

    def test_send_login_code_rate_limit_exceeded(self, rf: RequestFactory):
        """Test that send_login_code raises ValidationError when rate limit is exceeded."""
        # Create a user
        user = UserFactory()

        # Create a request
        request = rf.get("/fake-url/")
        request.META["REMOTE_ADDR"] = "127.0.0.1"

        # Create 5 LoginCodeRequest objects for this user and IP
        for _ in range(5):
            LoginCodeRequest.objects.create(
                email=user.email,
                ip_address="127.0.0.1",
                requested_at=timezone.now()
            )

        # Create a mock adapter
        adapter = MockAccountAdapter()

        # Call the method and expect a ValidationError
        with pytest.raises(ValidationError) as excinfo:
            adapter.send_login_code(request, user)

        # Check the error message
        assert "Too many login code requests" in str(excinfo.value)

        # Check that the parent method would not have been called
        assert adapter.parent_called is False

    def test_send_login_code_old_requests_ignored(self, rf: RequestFactory):
        """Test that old requests are not counted towards the rate limit."""
        # Create a user
        user = UserFactory()

        # Create a request
        request = rf.get("/fake-url/")
        request.META["REMOTE_ADDR"] = "127.0.0.1"

        # Create 5 old LoginCodeRequest objects for this user and IP
        for _ in range(5):
            LoginCodeRequest.objects.create(
                email=user.email,
                ip_address="127.0.0.1",
                requested_at=timezone.now() - timedelta(minutes=11)  # Older than the 10-minute window
            )

        # Create a mock adapter
        adapter = MockAccountAdapter()

        # Call the method - should not raise an error
        adapter.send_login_code(request, user)

        # Check that a new LoginCodeRequest was created
        assert LoginCodeRequest.objects.filter(
            email=user.email,
            ip_address="127.0.0.1",
            requested_at__gte=timezone.now() - timedelta(minutes=1)
        ).exists()

        # Check that the parent method would have been called
        assert adapter.parent_called is True

    @patch('learnmusic.users.adapters.send_mail')
    def test_save_user_sends_email(self, mock_send_mail, rf: RequestFactory, settings):
        """Test that save_user sends an email to admin when a user signs up."""
        # Configure settings
        settings.ADMINS = [("Admin", "admin@example.com")]
        settings.DEFAULT_FROM_EMAIL = "noreply@example.com"

        # Create a user
        user = UserFactory()

        # Create a request
        request = rf.get("/fake-url/")

        # Create a form mock
        form = MagicMock()

        # Create an adapter
        adapter = AccountAdapter()

        # Mock the parent save_user method
        with patch.object(AccountAdapter, 'save_user', return_value=user) as mock_parent_save_user:
            # Call the method
            result = adapter.save_user(request, user, form)

            # Check that the parent method was called
            mock_parent_save_user.assert_called_once_with(request, user, form, True)

            # Check that send_mail was called with the correct arguments
            mock_send_mail.assert_called_once_with(
                subject="New User Registration",
                message=f"A new user has registered on LearnMusic:\n\nEmail: {user.email}\nName: {user.name}",
                from_email="noreply@example.com",
                recipient_list=["admin@example.com"],
                fail_silently=True,
            )

            # Check that the method returns the user
            assert result == user

    @patch('learnmusic.users.adapters.send_mail')
    def test_save_user_no_default_from_email(self, mock_send_mail, rf: RequestFactory, settings):
        """Test that save_user works when DEFAULT_FROM_EMAIL is not set."""
        # Configure settings
        settings.ADMINS = [("Admin", "admin@example.com")]
        delattr(settings, 'DEFAULT_FROM_EMAIL') if hasattr(settings, 'DEFAULT_FROM_EMAIL') else None

        # Create a user
        user = UserFactory()

        # Create a request
        request = rf.get("/fake-url/")

        # Create a form mock
        form = MagicMock()

        # Create an adapter
        adapter = AccountAdapter()

        # Mock the parent save_user method
        with patch.object(AccountAdapter, 'save_user', return_value=user) as mock_parent_save_user:
            # Call the method
            result = adapter.save_user(request, user, form)

            # Check that the parent method was called
            mock_parent_save_user.assert_called_once_with(request, user, form, True)

            # Check that send_mail was called with the correct arguments
            mock_send_mail.assert_called_once_with(
                subject="New User Registration",
                message=f"A new user has registered on LearnMusic:\n\nEmail: {user.email}\nName: {user.name}",
                from_email=None,
                recipient_list=["admin@example.com"],
                fail_silently=True,
            )

            # Check that the method returns the user
            assert result == user

    @patch('learnmusic.users.adapters.send_mail')
    def test_save_user_no_admins(self, mock_send_mail, rf: RequestFactory, settings):
        """Test that save_user doesn't send an email when ADMINS is empty."""
        # Configure settings
        settings.ADMINS = []

        # Create a user
        user = UserFactory()

        # Create a request
        request = rf.get("/fake-url/")

        # Create a form mock
        form = MagicMock()

        # Create an adapter
        adapter = AccountAdapter()

        # Mock the parent save_user method
        with patch.object(AccountAdapter, 'save_user', return_value=user) as mock_parent_save_user:
            # Call the method
            result = adapter.save_user(request, user, form)

            # Check that the parent method was called
            mock_parent_save_user.assert_called_once_with(request, user, form, True)

            # Check that send_mail was not called
            mock_send_mail.assert_not_called()

            # Check that the method returns the user
            assert result == user


class TestSocialAccountAdapter:
    @patch('learnmusic.users.adapters.send_mail')
    def test_save_user_sends_email(self, mock_send_mail, rf: RequestFactory, settings):
        """Test that save_user sends an email to admin when a user signs up via social login."""
        # Configure settings
        settings.ADMINS = [("Admin", "admin@example.com")]
        settings.DEFAULT_FROM_EMAIL = "noreply@example.com"

        # Create a user
        user = UserFactory()

        # Create a request
        request = rf.get("/fake-url/")

        # Create a mock SocialLogin object
        sociallogin = MagicMock()
        sociallogin.account.provider = "google"

        # Create an adapter
        adapter = SocialAccountAdapter()

        # Mock the parent save_user method
        with patch.object(SocialAccountAdapter, 'save_user', return_value=user) as mock_parent_save_user:
            # Call the method
            result = adapter.save_user(request, sociallogin)

            # Check that the parent method was called
            mock_parent_save_user.assert_called_once_with(request, sociallogin, None)

            # Check that send_mail was called with the correct arguments
            mock_send_mail.assert_called_once_with(
                subject="New Google Social Login",
                message=f"A new user has registered on LearnMusic using Google:\n\nEmail: {user.email}\nName: {user.name}",
                from_email="noreply@example.com",
                recipient_list=["admin@example.com"],
                fail_silently=True,
            )

            # Check that the method returns the user
            assert result == user

    @patch('learnmusic.users.adapters.send_mail')
    def test_save_user_different_provider(self, mock_send_mail, rf: RequestFactory, settings):
        """Test that save_user works with different social providers."""
        # Configure settings
        settings.ADMINS = [("Admin", "admin@example.com")]
        settings.DEFAULT_FROM_EMAIL = "noreply@example.com"

        # Create a user
        user = UserFactory()

        # Create a request
        request = rf.get("/fake-url/")

        # Create a mock SocialLogin object with Apple provider
        sociallogin = MagicMock()
        sociallogin.account.provider = "apple"

        # Create an adapter
        adapter = SocialAccountAdapter()

        # Mock the parent save_user method
        with patch.object(SocialAccountAdapter, 'save_user', return_value=user) as mock_parent_save_user:
            # Call the method
            result = adapter.save_user(request, sociallogin)

            # Check that the parent method was called
            mock_parent_save_user.assert_called_once_with(request, sociallogin, None)

            # Check that send_mail was called with the correct arguments
            mock_send_mail.assert_called_once_with(
                subject="New Apple Social Login",
                message=f"A new user has registered on LearnMusic using Apple:\n\nEmail: {user.email}\nName: {user.name}",
                from_email="noreply@example.com",
                recipient_list=["admin@example.com"],
                fail_silently=True,
            )

            # Check that the method returns the user
            assert result == user

    @patch('learnmusic.users.adapters.send_mail')
    def test_save_user_no_default_from_email(self, mock_send_mail, rf: RequestFactory, settings):
        """Test that save_user works when DEFAULT_FROM_EMAIL is not set."""
        # Configure settings
        settings.ADMINS = [("Admin", "admin@example.com")]
        delattr(settings, 'DEFAULT_FROM_EMAIL') if hasattr(settings, 'DEFAULT_FROM_EMAIL') else None

        # Create a user
        user = UserFactory()

        # Create a request
        request = rf.get("/fake-url/")

        # Create a mock SocialLogin object
        sociallogin = MagicMock()
        sociallogin.account.provider = "google"

        # Create an adapter
        adapter = SocialAccountAdapter()

        # Mock the parent save_user method
        with patch.object(SocialAccountAdapter, 'save_user', return_value=user) as mock_parent_save_user:
            # Call the method
            result = adapter.save_user(request, sociallogin)

            # Check that the parent method was called
            mock_parent_save_user.assert_called_once_with(request, sociallogin, None)

            # Check that send_mail was called with the correct arguments
            mock_send_mail.assert_called_once_with(
                subject="New Google Social Login",
                message=f"A new user has registered on LearnMusic using Google:\n\nEmail: {user.email}\nName: {user.name}",
                from_email=None,
                recipient_list=["admin@example.com"],
                fail_silently=True,
            )

            # Check that the method returns the user
            assert result == user

    @patch('learnmusic.users.adapters.send_mail')
    def test_save_user_no_admins(self, mock_send_mail, rf: RequestFactory, settings):
        """Test that save_user doesn't send an email when ADMINS is empty."""
        # Configure settings
        settings.ADMINS = []

        # Create a user
        user = UserFactory()

        # Create a request
        request = rf.get("/fake-url/")

        # Create a mock SocialLogin object
        sociallogin = MagicMock()
        sociallogin.account.provider = "google"

        # Create an adapter
        adapter = SocialAccountAdapter()

        # Mock the parent save_user method
        with patch.object(SocialAccountAdapter, 'save_user', return_value=user) as mock_parent_save_user:
            # Call the method
            result = adapter.save_user(request, sociallogin)

            # Check that the parent method was called
            mock_parent_save_user.assert_called_once_with(request, sociallogin, None)

            # Check that send_mail was not called
            mock_send_mail.assert_not_called()

            # Check that the method returns the user
            assert result == user
