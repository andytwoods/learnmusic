"""
Tests for the tasks.py module, focusing on the send_reminders function.
"""
import datetime
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.utils import timezone

from notes.factories import UserFactory, LearningScenarioFactory
from notes.models import NoteRecord, LearningScenario
from notes.tasks import send_reminders


class TestSendReminders(TestCase):
    """Test cases for the send_reminders function."""

    def setUp(self):
        """Set up test data."""
        # Current time for testing
        self.now = timezone.now()
        # Time 25 hours ago (for testing reminders over 24 hours old)
        self.time_25_hours_ago = self.now - timezone.timedelta(hours=25)

    @patch('notes.tasks.PushoverAPI')
    @patch('notes.tasks.send_mail')
    def test_send_reminders_email_only(self, mock_send_mail, mock_pushover_api):
        """Test that reminders are sent via email only when reminder_type is 'EM'."""
        # Set up mocks
        mock_pushover_instance = MagicMock()
        mock_pushover_api.return_value = mock_pushover_instance

        # Create a test scenario for this test only
        user = UserFactory(email="email_only@example.com", pushover_key="email_only_key")
        scenario = LearningScenarioFactory(
            user=user,
            reminder=self.time_25_hours_ago.replace(hour=self.now.hour),  # Set reminder time to 25 hours ago but same hour
            reminder_type=LearningScenario.Reminder.EMAIL,
            reminder_sent=None  # No reminder sent yet
        )

        # Call the function
        send_reminders()

        # Check that email was sent for the scenario
        self.assertEqual(mock_send_mail.call_count, 1)

        # Check that Pushover notification was not sent
        mock_pushover_instance.send_message.assert_not_called()

        # Check that reminder_sent was updated
        scenario.refresh_from_db()
        self.assertIsNotNone(scenario.reminder_sent)
        self.assertEqual(scenario.reminder_sent.date(), timezone.now().date())

    @patch('notes.tasks.PushoverAPI')
    @patch('notes.tasks.send_mail')
    def test_send_reminders_already_practiced(self, mock_send_mail, mock_pushover_api):
        """Test that reminders are not sent when the user has already practiced today."""
        # Set up mocks
        mock_pushover_instance = MagicMock()
        mock_pushover_api.return_value = mock_pushover_instance

        # Create a test scenario for this test only
        user = UserFactory(email="already_practiced@example.com", pushover_key="already_practiced_key")
        scenario = LearningScenarioFactory(
            user=user,
            reminder=self.time_25_hours_ago.replace(hour=self.now.hour),  # Set reminder time to 25 hours ago but same hour
            reminder_type=LearningScenario.Reminder.PUSH_NOTIFICATION,
            reminder_sent=None  # No reminder sent yet
        )

        # Create a note record for today to simulate that user has already practiced
        NoteRecord.objects.create(
            learningscenario=scenario,
            note="C",
            alter="",
            octave="4",
            reaction_time=500,
            correct=True
        )

        # Call the function
        send_reminders()

        # Check that no notification was sent
        mock_pushover_instance.send_message.assert_not_called()
        mock_send_mail.assert_not_called()

        # Check that reminder_sent was not updated
        scenario.refresh_from_db()
        self.assertIsNone(scenario.reminder_sent)

    @patch('notes.tasks.PushoverAPI')
    @patch('notes.tasks.send_mail')
    def test_send_reminders_already_sent(self, mock_send_mail, mock_pushover_api):
        """Test that reminders are not sent when a reminder has already been sent today."""
        # Set up mocks
        mock_pushover_instance = MagicMock()
        mock_pushover_api.return_value = mock_pushover_instance

        # Create a test scenario for this test only
        user = UserFactory(email="already_sent@example.com", pushover_key="already_sent_key")
        reminder_sent_time = timezone.now()
        scenario = LearningScenarioFactory(
            user=user,
            reminder=self.time_25_hours_ago.replace(hour=self.now.hour),  # Set reminder time to 25 hours ago but same hour
            reminder_type=LearningScenario.Reminder.ALL,
            reminder_sent=reminder_sent_time  # Reminder already sent today
        )

        # Call the function
        send_reminders()

        # Check that no notification was sent
        mock_pushover_instance.send_message.assert_not_called()
        mock_send_mail.assert_not_called()

        # Check that reminder_sent was not updated
        scenario.refresh_from_db()
        self.assertEqual(scenario.reminder_sent, reminder_sent_time)

    @patch('notes.tasks.PushoverAPI')
    @patch('notes.tasks.send_mail')
    def test_send_reminders_wrong_time(self, mock_send_mail, mock_pushover_api):
        """Test that reminders are not sent when it's not the right time."""
        # Set up mocks
        mock_pushover_instance = MagicMock()
        mock_pushover_api.return_value = mock_pushover_instance

        # Create a test scenario for this test only
        user = UserFactory(email="wrong_time@example.com", pushover_key="wrong_time_key")
        scenario = LearningScenarioFactory(
            user=user,
            reminder=self.time_25_hours_ago.replace(hour=(self.now.hour + 2) % 24),  # Set reminder time to 25 hours ago but 2 hours different
            reminder_type=LearningScenario.Reminder.ALL,
            reminder_sent=None  # No reminder sent yet
        )

        # Call the function
        send_reminders()

        # Check that no notification was sent
        mock_pushover_instance.send_message.assert_not_called()
        mock_send_mail.assert_not_called()

        # Check that reminder_sent was not updated
        scenario.refresh_from_db()
        self.assertIsNone(scenario.reminder_sent)

    @patch('notes.tasks.PushoverAPI')
    @patch('notes.tasks.send_mail')
    def test_send_reminders_push_notification_only(self, mock_send_mail, mock_pushover_api):
        """Test that reminders are sent via push notification only when reminder_type is 'PN'."""
        # Set up mocks
        mock_pushover_instance = MagicMock()
        mock_pushover_api.return_value = mock_pushover_instance

        # Create a test scenario for this test only
        user = UserFactory(email="push_only@example.com", pushover_key="push_only_key")
        scenario = LearningScenarioFactory(
            user=user,
            reminder=self.time_25_hours_ago.replace(hour=self.now.hour),  # Set reminder time to 25 hours ago but same hour
            reminder_type=LearningScenario.Reminder.PUSH_NOTIFICATION,
            reminder_sent=None  # No reminder sent yet
        )

        # Call the function
        send_reminders()

        # Check that Pushover notification was sent
        mock_pushover_instance.send_message.assert_called_once()

        # Check that email was not sent
        mock_send_mail.assert_not_called()

        # Check that reminder_sent was updated
        scenario.refresh_from_db()
        self.assertIsNotNone(scenario.reminder_sent)
        self.assertEqual(scenario.reminder_sent.date(), timezone.now().date())

    @patch('notes.tasks.PushoverAPI')
    @patch('notes.tasks.send_mail')
    def test_send_reminders_all_notifications(self, mock_send_mail, mock_pushover_api):
        """Test that reminders are sent via both email and push notification when reminder_type is 'AL'."""
        # Set up mocks
        mock_pushover_instance = MagicMock()
        mock_pushover_api.return_value = mock_pushover_instance

        # Create a test scenario for this test only
        user = UserFactory(email="all_notifications@example.com", pushover_key="all_notifications_key")
        scenario = LearningScenarioFactory(
            user=user,
            reminder=self.time_25_hours_ago.replace(hour=self.now.hour),  # Set reminder time to 25 hours ago but same hour
            reminder_type=LearningScenario.Reminder.ALL,
            reminder_sent=None  # No reminder sent yet
        )

        # Call the function
        send_reminders()

        # Check that both email and Pushover notification were sent
        mock_pushover_instance.send_message.assert_called_once()
        self.assertEqual(mock_send_mail.call_count, 1)

        # Check that reminder_sent was updated
        scenario.refresh_from_db()
        self.assertIsNotNone(scenario.reminder_sent)
        self.assertEqual(scenario.reminder_sent.date(), timezone.now().date())

    @patch('notes.tasks.PushoverAPI')
    @patch('notes.tasks.send_mail')
    def test_send_reminders_over_24_hours(self, mock_send_mail, mock_pushover_api):
        """Test that reminders are only sent for scenarios with reminders over 24 hours old."""
        # Set up mocks
        mock_pushover_instance = MagicMock()
        mock_pushover_api.return_value = mock_pushover_instance

        # Create a user for both scenarios
        user = UserFactory(email="reminder_age_test@example.com", pushover_key="reminder_age_key")

        # Create a scenario with a reminder over 24 hours old
        old_reminder_time = self.now - datetime.timedelta(hours=25)
        old_scenario = LearningScenarioFactory(
            user=user,
            reminder=old_reminder_time.replace(hour=self.now.hour),  # Set hour to current hour
            reminder_type=LearningScenario.Reminder.EMAIL,
            reminder_sent=None  # No reminder sent yet
        )

        # Create a scenario with a recent reminder (less than 24 hours old)
        recent_reminder_time = self.now - datetime.timedelta(hours=12)
        recent_scenario = LearningScenarioFactory(
            user=user,
            reminder=recent_reminder_time.replace(hour=self.now.hour),  # Set hour to current hour
            reminder_type=LearningScenario.Reminder.EMAIL,
            reminder_sent=None  # No reminder sent yet
        )

        # Call the function
        send_reminders()

        # Check that email was sent only once (for the old scenario)
        self.assertEqual(mock_send_mail.call_count, 1)

        # Check that reminder_sent was updated only for the old scenario
        old_scenario.refresh_from_db()
        recent_scenario.refresh_from_db()

        self.assertIsNotNone(old_scenario.reminder_sent)
        self.assertIsNone(recent_scenario.reminder_sent)
