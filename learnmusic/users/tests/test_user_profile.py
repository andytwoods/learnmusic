from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from notes.factories import UserFactory
from learnmusic.users.models import UserProfile


class TestUserProfile(TestCase):
    """
    Tests for the UserProfile model.
    """

    def setUp(self):
        """
        Set up test data.
        """
        self.user = UserFactory()

    def test_profile_creation(self):
        """
        Test that a profile is automatically created when accessing user.profile.
        """
        # Access the profile property to create the profile
        profile = self.user.profile

        # Check that the profile was created
        self.assertIsInstance(profile, UserProfile)
        self.assertEqual(profile.user, self.user)

        # Check default values
        self.assertEqual(profile.reminder_time, "18:00")
        self.assertEqual(profile.timezone, "UTC")
        self.assertIsNone(profile.reminder_sent)

    def test_profile_update(self):
        """
        Test updating the profile.
        """
        # Access the profile property to create the profile
        profile = self.user.profile

        # Update the profile
        profile.reminder_time = "09:00"
        profile.timezone = "Europe/London"
        profile.reminder_sent = timezone.now()
        profile.save()

        # Refresh from the database
        profile.refresh_from_db()

        # Check that the updates were saved
        self.assertEqual(profile.reminder_time, "09:00")
        self.assertEqual(profile.timezone, "Europe/London")
        self.assertIsNotNone(profile.reminder_sent)

    def test_reminder_sent_today(self):
        """
        Test checking if a reminder was sent today.
        """
        # Access the profile property to create the profile
        profile = self.user.profile

        # Set reminder_sent to today
        now = timezone.now()
        profile.reminder_sent = now
        profile.save()

        # Check that reminder_sent.date() equals today
        self.assertEqual(profile.reminder_sent.date(), now.date())

    def test_reminder_sent_yesterday(self):
        """
        Test checking if a reminder was sent yesterday.
        """
        # Access the profile property to create the profile
        profile = self.user.profile

        # Set reminder_sent to yesterday
        yesterday = timezone.now() - timedelta(days=1)
        profile.reminder_sent = yesterday
        profile.save()

        # Check that reminder_sent.date() equals yesterday
        self.assertEqual(profile.reminder_sent.date(), yesterday.date())

        # Check that reminder_sent.date() does not equal today
        self.assertNotEqual(profile.reminder_sent.date(), timezone.now().date())

    def test_disabled_reminders(self):
        """
        Test setting reminders to disabled.
        """
        # Access the profile property to create the profile
        profile = self.user.profile

        # Set reminder_time to DISABLED
        profile.reminder_time = "DISABLED"
        profile.save()

        # Check that reminder_time is DISABLED
        self.assertEqual(profile.reminder_time, "DISABLED")

    def test_string_representation(self):
        """
        Test the string representation of the UserProfile model.
        """
        # Access the profile property to create the profile
        profile = self.user.profile

        # Check the string representation
        expected_string = f"{self.user.email}'s Profile"
        self.assertEqual(str(profile), expected_string)
