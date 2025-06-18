import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.utils import timezone
from zoneinfo import ZoneInfo

from notes.factories import UserFactory, LearningScenarioFactory
from notes.models import NoteRecord
from notes.tasks import send_reminders
from learnmusic.users.models import UserProfile


class UserProfileFactory:
    """
    Factory for creating UserProfile objects for testing.
    """
    @staticmethod
    def create(user=None, reminder_time="18:00", timezone_name="UTC", reminder_sent=None, convert_to_utc=False):
        """
        Create a UserProfile with the given parameters.

        Args:
            user: The user to create the profile for. If None, a new user will be created.
            reminder_time: The reminder time in HH:MM format.
            timezone_name: The timezone name.
            reminder_sent: The datetime when the last reminder was sent.
            convert_to_utc: If True, convert the reminder_time from the specified timezone to UTC.
                           If False, use the reminder_time as-is (assuming it's already in UTC).
        """
        if user is None:
            user = UserFactory()

        profile = user.profile  # This will create the profile if it doesn't exist

        # Convert the reminder time to UTC if requested
        if convert_to_utc and reminder_time != "DISABLED":
            # Parse the local time (HH:MM)
            hour, minute = map(int, reminder_time.split(':'))

            # Create a datetime object for today at the specified time in the user's timezone
            user_tz = ZoneInfo(timezone_name)
            now = datetime.now(user_tz)
            local_dt = datetime(now.year, now.month, now.day, hour, minute, tzinfo=user_tz)

            # Convert to UTC
            utc_dt = local_dt.astimezone(ZoneInfo("UTC"))

            # Format as HH:MM
            reminder_time = utc_dt.strftime("%H:%M")

        profile.reminder_time = reminder_time
        profile.timezone = timezone_name
        profile.reminder_sent = reminder_sent
        profile.save()

        return profile


class TestSendReminders(TestCase):
    """
    Tests for the send_reminders function in tasks.py.
    """

    def setUp(self):
        """
        Set up test data.
        """
        # Create users with different reminder settings
        self.user1 = UserFactory()
        self.user2 = UserFactory()
        self.user3 = UserFactory()
        self.user4 = UserFactory()
        self.user5 = UserFactory()

        # User 1: Normal user with reminder time set to current hour
        current_hour = datetime.now().strftime("%H:00")
        UserProfileFactory.create(user=self.user1, reminder_time=current_hour)

        # User 2: User who has already received a reminder today
        UserProfileFactory.create(
            user=self.user2,
            reminder_time=current_hour,
            reminder_sent=timezone.now()
        )

        # User 3: User with reminder time set to a different hour
        different_hour = (datetime.now() + timedelta(hours=3)).strftime("%H:00")
        UserProfileFactory.create(user=self.user3, reminder_time=different_hour)

        # User 4: User with reminders disabled
        UserProfileFactory.create(user=self.user4, reminder_time="DISABLED")

        # User 5: User who has already practiced today
        UserProfileFactory.create(user=self.user5, reminder_time=current_hour)

        # Create a learning scenario for user 5 and add a note record for today
        self.scenario = LearningScenarioFactory(user=self.user5)
        self.note_record = NoteRecord.objects.create(
            learningscenario=self.scenario,
            note="C",
            alter="0",
            octave="4",
            reaction_time=1000,
            correct=True
        )

    @patch('notes.tasks.send_user_notification')
    def test_send_reminders_to_eligible_users(self, mock_send_notification):
        """
        Test that reminders are sent to eligible users (those who haven't practiced today
        and haven't received a reminder today, and whose reminder time is within the current hour).
        """
        # Run the send_reminders function
        send_reminders()

        # Check that send_user_notification was called once for user1
        self.assertEqual(mock_send_notification.call_count, 1)

        # Check that the call was for user1
        args, kwargs = mock_send_notification.call_args
        self.assertEqual(kwargs['user'], self.user1)

        # Check that user1's reminder_sent field was updated
        self.user1.refresh_from_db()
        self.assertIsNotNone(self.user1.profile.reminder_sent)
        self.assertEqual(self.user1.profile.reminder_sent.date(), timezone.now().date())

    @patch('notes.tasks.send_user_notification')
    def test_no_reminder_for_users_who_already_received_reminder(self, mock_send_notification):
        """
        Test that reminders are not sent to users who have already received a reminder today.
        """
        # Run the send_reminders function
        send_reminders()

        # Check that send_user_notification was not called for user2
        for call in mock_send_notification.call_args_list:
            args, kwargs = call
            self.assertNotEqual(kwargs['user'], self.user2)

    @patch('notes.tasks.send_user_notification')
    def test_no_reminder_for_users_outside_reminder_time(self, mock_send_notification):
        """
        Test that reminders are not sent to users whose reminder time is not within the current hour.
        """
        # Run the send_reminders function
        send_reminders()

        # Check that send_user_notification was not called for user3
        for call in mock_send_notification.call_args_list:
            args, kwargs = call
            self.assertNotEqual(kwargs['user'], self.user3)

    @patch('notes.tasks.send_user_notification')
    def test_no_reminder_for_users_with_disabled_reminders(self, mock_send_notification):
        """
        Test that reminders are not sent to users who have disabled reminders.
        """
        # Run the send_reminders function
        send_reminders()

        # Check that send_user_notification was not called for user4
        for call in mock_send_notification.call_args_list:
            args, kwargs = call
            self.assertNotEqual(kwargs['user'], self.user4)

    @patch('notes.tasks.send_user_notification')
    def test_no_reminder_for_users_who_practiced_today(self, mock_send_notification):
        """
        Test that reminders are not sent to users who have already practiced today.
        """
        # Run the send_reminders function
        send_reminders()

        # Check that send_user_notification was not called for user5
        for call in mock_send_notification.call_args_list:
            args, kwargs = call
            self.assertNotEqual(kwargs['user'], self.user5)

    @patch('notes.tasks.send_user_notification')
    def test_reminder_sent_field_updated(self, mock_send_notification):
        """
        Test that the reminder_sent field is updated when a reminder is sent.
        """
        # Set up a user who should receive a reminder
        user = UserFactory()
        current_hour = datetime.now().strftime("%H:00")
        UserProfileFactory.create(user=user, reminder_time=current_hour)

        # Run the send_reminders function
        send_reminders()

        # Check that the reminder_sent field was updated
        user.refresh_from_db()
        self.assertIsNotNone(user.profile.reminder_sent)
        self.assertEqual(user.profile.reminder_sent.date(), timezone.now().date())

    @patch('notes.tasks.send_user_notification', side_effect=Exception("Test exception"))
    def test_exception_handling(self, mock_send_notification):
        """
        Test that exceptions during notification sending are handled gracefully.
        """
        # Set up a user who should receive a reminder
        user = UserFactory()
        current_hour = datetime.now().strftime("%H:00")
        UserProfileFactory.create(user=user, reminder_time=current_hour)

        # Run the send_reminders function - it should not raise an exception
        try:
            send_reminders()
        except Exception:
            self.fail("send_reminders() raised an exception unexpectedly!")

        # Check that the function attempted to send a notification
        mock_send_notification.assert_called_once()

    @patch('notes.tasks.send_user_notification')
    def test_utc_reminder_time(self, mock_send_notification):
        """
        Test that reminders are sent based on UTC time, not local time.
        """
        # Get the current UTC hour
        now_utc = timezone.now()
        current_utc_hour = now_utc.hour

        # Create a user with a reminder time set to the current UTC hour
        user = UserFactory()
        utc_reminder_time = f"{current_utc_hour:02d}:00"

        # Set the user's timezone to a non-UTC timezone
        UserProfileFactory.create(
            user=user,
            reminder_time=utc_reminder_time,
            timezone_name="America/New_York"  # UTC-5 or UTC-4 depending on DST
        )

        # Run the send_reminders function
        send_reminders()

        # Check that send_user_notification was called for the user
        # This verifies that the reminder was sent based on the UTC time,
        # not the local time in the user's timezone
        self.assertEqual(mock_send_notification.call_count, 1)
        args, kwargs = mock_send_notification.call_args
        self.assertEqual(kwargs['user'], user)

    @patch('notes.tasks.send_user_notification')
    def test_multiple_timezones(self, mock_send_notification):
        """
        Test that reminders are sent correctly to users in different time zones.
        """
        # Get the current UTC hour
        now_utc = timezone.now()
        current_utc_hour = now_utc.hour
        utc_reminder_time = f"{current_utc_hour:02d}:00"

        # Test with multiple different timezones
        timezones_to_test = [
            "UTC",                # UTC+0
            "Europe/London",      # UTC+0/+1
            "Europe/Paris",       # UTC+1/+2
            "Asia/Tokyo",         # UTC+9
            "Australia/Sydney",   # UTC+10/+11
            "Pacific/Auckland",   # UTC+12/+13
            "America/Los_Angeles" # UTC-8/-7
        ]

        # Create users in different time zones, all with reminder times set to the current UTC hour
        users = []
        for tz_name in timezones_to_test:
            user = UserFactory()
            UserProfileFactory.create(
                user=user,
                reminder_time=utc_reminder_time,
                timezone_name=tz_name
            )
            users.append(user)

        # Run the send_reminders function
        send_reminders()

        # Check that send_user_notification was called for each user
        self.assertEqual(mock_send_notification.call_count, len(timezones_to_test))

        # Check that each user received a notification
        called_users = [kwargs['user'] for args, kwargs in mock_send_notification.call_args_list]
        for user in users:
            self.assertIn(user, called_users, f"User with timezone {user.profile.timezone} did not receive a notification")

    @patch('notes.tasks.send_user_notification')
    def test_local_time_conversion(self, mock_send_notification):
        """
        Test that users receive reminders at their specified local time, properly converted to UTC.
        """
        # Test with multiple different timezones and local times
        timezone_local_time_pairs = [
            ("UTC", "12:00"),                # Noon UTC
            ("Europe/London", "13:00"),      # 1 PM London time
            ("Europe/Paris", "14:00"),       # 2 PM Paris time
            ("Asia/Tokyo", "21:00"),         # 9 PM Tokyo time
            ("America/Los_Angeles", "08:00") # 8 AM Los Angeles time
        ]

        # Create users in different time zones with different local reminder times
        users = []
        for tz_name, local_time in timezone_local_time_pairs:
            user = UserFactory()
            # Convert local time to UTC for storage
            UserProfileFactory.create(
                user=user,
                reminder_time=local_time,
                timezone_name=tz_name,
                convert_to_utc=True  # This will convert the local time to UTC
            )
            users.append(user)

        # Mock the current UTC time to be noon
        with patch('notes.tasks.timezone.now') as mock_now:
            # Set the current time to noon UTC
            mock_now.return_value = datetime.now(ZoneInfo("UTC")).replace(hour=12, minute=0)

            # Run the send_reminders function
            send_reminders()

            # Check that send_user_notification was called only for the UTC user
            # (since we mocked the current time to be noon UTC)
            self.assertEqual(mock_send_notification.call_count, 1)

            # Check that the UTC user received a notification
            args, kwargs = mock_send_notification.call_args
            self.assertEqual(kwargs['user'], users[0])

        # Reset the mock
        mock_send_notification.reset_mock()

        # Now mock the current UTC time to be 1 PM UTC
        with patch('notes.tasks.timezone.now') as mock_now:
            # Set the current time to 1 PM UTC
            mock_now.return_value = datetime.now(ZoneInfo("UTC")).replace(hour=13, minute=0)

            # Run the send_reminders function
            send_reminders()

            # Check that send_user_notification was called only for the London user
            self.assertEqual(mock_send_notification.call_count, 1)

            # Check that the London user received a notification
            args, kwargs = mock_send_notification.call_args
            self.assertEqual(kwargs['user'], users[1])

    @patch('notes.tasks.send_user_notification')
    def test_edge_case_timezones(self, mock_send_notification):
        """
        Test that reminders work correctly for users in edge case time zones,
        such as those with unusual UTC offsets or near the International Date Line.
        """
        # Test with edge case timezones
        edge_case_timezones = [
            "Pacific/Chatham",     # UTC+12:45/+13:45 (unusual offset)
            "Pacific/Kiritimati",  # UTC+14 (furthest ahead)
            "Pacific/Niue",        # UTC-11 (furthest behind)
            "Asia/Kathmandu",      # UTC+5:45 (unusual offset)
            "Australia/Eucla",     # UTC+8:45 (unusual offset)
            "Pacific/Marquesas",   # UTC-9:30 (unusual offset)
        ]

        # Create users in different edge case time zones
        users = []

        # Use a fixed local time (noon) for all users
        local_time = "12:00"  # Noon local time

        for tz_name in edge_case_timezones:
            user = UserFactory()
            # Convert local time to UTC for storage
            UserProfileFactory.create(
                user=user,
                reminder_time=local_time,
                timezone_name=tz_name,
                convert_to_utc=True  # This will convert the local time to UTC
            )
            users.append(user)

        # For each user, mock the current UTC time to match their reminder time
        # and verify they receive a notification
        for i, user in enumerate(users):
            # Reset the mock
            mock_send_notification.reset_mock()

            # Get the user's UTC reminder time
            utc_reminder_hour, utc_reminder_minute = map(int, user.profile.reminder_time.split(':'))

            # Mock the current UTC time to match the user's reminder time
            with patch('notes.tasks.timezone.now') as mock_now:
                mock_now.return_value = datetime.now(ZoneInfo("UTC")).replace(
                    hour=utc_reminder_hour,
                    minute=utc_reminder_minute
                )

                # Run the send_reminders function
                send_reminders()

                # Check that send_user_notification was called for this user
                self.assertEqual(mock_send_notification.call_count, 1,
                                f"No notification sent for user in {user.profile.timezone}")

                # Check that this user received a notification
                args, kwargs = mock_send_notification.call_args
                self.assertEqual(kwargs['user'], user,
                                f"Wrong user received notification for {user.profile.timezone}")

    @patch('notes.tasks.send_user_notification')
    def test_date_boundary_cases(self, mock_send_notification):
        """
        Test that reminders work correctly for users across date boundaries.
        """
        # Create two users, one in UTC and one in UTC+12
        utc_user = UserFactory()
        UserProfileFactory.create(
            user=utc_user,
            reminder_time="23:00",  # 11 PM UTC
            timezone_name="UTC"
        )

        date_line_user = UserFactory()
        UserProfileFactory.create(
            user=date_line_user,
            reminder_time="11:00",  # 11 AM UTC+12 (11 PM UTC)
            timezone_name="Pacific/Auckland",
            convert_to_utc=True
        )

        # Mock the current UTC time to be 11 PM
        with patch('notes.tasks.timezone.now') as mock_now:
            # Set the current time to 11 PM UTC
            mock_now.return_value = datetime.now(ZoneInfo("UTC")).replace(hour=23, minute=0)

            # Also mock the date check to ensure both users get notifications
            with patch('notes.tasks.NoteRecord.objects.filter') as mock_filter:
                mock_filter.return_value.exists.return_value = False

                # Run the send_reminders function
                send_reminders()

                # Check that send_user_notification was called for both users
                self.assertEqual(mock_send_notification.call_count, 2,
                                "Both users should receive notifications")

                # Check that both users received notifications
                called_users = [kwargs['user'] for args, kwargs in mock_send_notification.call_args_list]
                self.assertIn(utc_user, called_users, "UTC user should receive a notification")
                self.assertIn(date_line_user, called_users, "Date line user should receive a notification")
