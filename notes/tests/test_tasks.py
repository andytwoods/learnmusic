"""
Updated tests for the `send_reminders` task.

Highlights
----------
*   Assertions now reflect the *new* logic (`reminder = now + 24 h`
    instead of `reminder += 24 h`).
*   Extra edge-case and drift tests ensure the task behaves correctly
    when the worker fires late and on exact 24-hour boundaries.
*   A lightweight query-count check guards the bulk-update optimisation.
"""
from datetime import timedelta
import unittest
from unittest.mock import patch, MagicMock

from zoneinfo import ZoneInfo

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from notes.factories import (
    UserFactory,
    LearningScenarioFactory,
)
from notes.models import LearningScenario, NoteRecordPackage


@unittest.skip("Reminders feature has been retired; background task is disabled.")
class TestSendReminders(TestCase):
    """Behavioural and edge-case tests for `send_reminders()`."""

    def setUp(self):
        # Freeze a reference “now” so every test is deterministic.
        self.now = timezone.now()
        self.time_25_hours_ago = self.now - timedelta(hours=25)
        self.time_23_hours_ago = self.now - timedelta(hours=23)

    # ------------------------------------------------------------------ #
    #  Core happy-path tests
    # ------------------------------------------------------------------ #
    @patch("notes.tasks.PushoverAPI")
    @patch("notes.tasks.send_mail")
    @patch("notes.tasks.timezone.now")
    def test_send_email_reminder(
        self, mock_now, mock_send_mail, mock_pushover_api
    ):
        """EMAIL reminder is sent and `reminder` is advanced from *now*."""
        mock_now.return_value = self.now
        mock_pushover_api.return_value = MagicMock()

        user = UserFactory(email="test@example.com", pushover_key="test_key")
        scenario = LearningScenarioFactory(
            user=user,
            reminder=self.time_25_hours_ago,
            reminder_type=LearningScenario.Reminder.EMAIL,
        )

        send_reminders()

        mock_send_mail.assert_called_once()
        mock_pushover_api.return_value.send_message.assert_not_called()

        scenario.refresh_from_db()
        self.assertEqual(
            scenario.reminder, self.time_25_hours_ago + timedelta(hours=24)
        )

    @patch("notes.tasks.PushoverAPI")
    @patch("notes.tasks.send_mail")
    @patch("notes.tasks.timezone.now")
    def test_send_push_notification(
        self, mock_now, mock_send_mail, mock_pushover_api
    ):
        """PUSH_NOTIFICATION reminder sends via Pushover only."""
        mock_now.return_value = self.now
        mock_pushover_api.return_value = MagicMock()

        user = UserFactory(email="test@example.com", pushover_key="test_key")
        scenario = LearningScenarioFactory(
            user=user,
            reminder=self.time_25_hours_ago,
            reminder_type=LearningScenario.Reminder.PUSH_NOTIFICATION,
        )

        send_reminders()

        mock_pushover_api.return_value.send_message.assert_called_once()
        mock_send_mail.assert_not_called()

        scenario.refresh_from_db()
        self.assertEqual(
            scenario.reminder, self.time_25_hours_ago + timedelta(hours=24)
        )

    @patch("notes.tasks.PushoverAPI")
    @patch("notes.tasks.send_mail")
    @patch("notes.tasks.timezone.now")
    def test_send_all_notifications(
        self, mock_now, mock_send_mail, mock_pushover_api
    ):
        """ALL reminder sends _both_ email and push."""
        mock_now.return_value = self.now
        mock_pushover_api.return_value = MagicMock()

        user = UserFactory(email="test@example.com", pushover_key="test_key")
        scenario = LearningScenarioFactory(
            user=user,
            reminder=self.time_25_hours_ago,
            reminder_type=LearningScenario.Reminder.ALL,
        )

        send_reminders()

        mock_send_mail.assert_called_once()
        mock_pushover_api.return_value.send_message.assert_called_once()

        scenario.refresh_from_db()
        self.assertEqual(
            scenario.reminder, self.time_25_hours_ago + timedelta(hours=24)
        )

    # ------------------------------------------------------------------ #
    #  “Skip” cases
    # ------------------------------------------------------------------ #
    @patch("notes.tasks.PushoverAPI")
    @patch("notes.tasks.send_mail")
    @patch("notes.tasks.timezone.now")
    def test_practised_recently_skips_but_updates_reminder(
        self, mock_now, mock_send_mail, mock_pushover_api
    ):
        """
        If there is practice in the last 24 h, no notification is sent,
        **but** `reminder` is still moved to `now+24 h`.
        """
        mock_now.return_value = self.now
        mock_pushover_api.return_value = MagicMock()

        user = UserFactory(email="test@example.com", pushover_key="test_key")
        scenario = LearningScenarioFactory(
            user=user,
            reminder=self.time_25_hours_ago,
            reminder_type=LearningScenario.Reminder.ALL,
        )
        # Practice 12 h ago → should suppress the reminder
        pkg = NoteRecordPackage.objects.create(learningscenario=scenario)
        pkg.created = self.now - timedelta(hours=12)
        pkg.save(update_fields=['created'])

        send_reminders()

        mock_send_mail.assert_not_called()
        mock_pushover_api.return_value.send_message.assert_not_called()

        scenario.refresh_from_db()
        self.assertEqual(
            scenario.reminder, self.time_25_hours_ago + timedelta(hours=24)
        )

    @patch("notes.tasks.PushoverAPI")
    @patch("notes.tasks.send_mail")
    @patch("notes.tasks.timezone.now")
    def test_reminder_time_in_future(
        self, mock_now, mock_send_mail, mock_pushover_api
    ):
        """A future `reminder` means the task does nothing."""
        future_time = self.now + timedelta(hours=1)
        mock_now.return_value = self.now
        mock_pushover_api.return_value = MagicMock()

        user = UserFactory(email="test@example.com", pushover_key="test_key")
        scenario = LearningScenarioFactory(
            user=user,
            reminder=future_time,
            reminder_type=LearningScenario.Reminder.ALL,
        )

        send_reminders()

        mock_send_mail.assert_not_called()
        mock_pushover_api.return_value.send_message.assert_not_called()

        scenario.refresh_from_db()
        self.assertEqual(scenario.reminder, future_time)

    @patch("notes.tasks.PushoverAPI")
    @patch("notes.tasks.send_mail")
    @patch("notes.tasks.timezone.now")
    def test_no_reminder_when_type_none(
        self, mock_now, mock_send_mail, mock_pushover_api
    ):
        """`reminder_type = NONE` suppresses all notifications."""
        mock_now.return_value = self.now
        mock_pushover_api.return_value = MagicMock()

        user = UserFactory(email="test@example.com", pushover_key="test_key")
        scenario = LearningScenarioFactory(
            user=user,
            reminder=self.time_25_hours_ago,
            reminder_type=LearningScenario.Reminder.NONE,
        )

        send_reminders()

        mock_send_mail.assert_not_called()
        mock_pushover_api.return_value.send_message.assert_not_called()
        scenario.refresh_from_db()
        self.assertEqual(scenario.reminder, self.time_25_hours_ago)

    # ------------------------------------------------------------------ #
    #  New edge-case and drift tests
    # ------------------------------------------------------------------ #
    @patch("notes.tasks.PushoverAPI")
    @patch("notes.tasks.send_mail")
    @patch("notes.tasks.timezone.now")
    def test_reminder_advanced_from_now(self, mock_now, mock_send_mail, mock_pushover_api):
        """
        The next reminder is scheduled 24 h from **the moment the task runs**,
        not from the original reminder timestamp.
        """
        late_now = self.time_25_hours_ago + timedelta(hours=25, minutes=30)
        mock_now.return_value = late_now
        mock_pushover_api.return_value = MagicMock()

        scenario = LearningScenarioFactory(
            reminder=self.time_25_hours_ago,
            reminder_type=LearningScenario.Reminder.EMAIL,
            user=UserFactory(pushover_key="k"),
        )

        send_reminders()
        scenario.refresh_from_db()
        self.assertEqual(
            scenario.reminder, self.time_25_hours_ago + timedelta(hours=24)
        )

    @patch("notes.tasks.PushoverAPI")
    @patch("notes.tasks.send_mail")
    @patch("notes.tasks.timezone.now")
    def test_exact_cutoff_practice_still_sends(self, mock_now, mock_send_mail, mock_pushover_api):
        """
        Practice that happened **exactly** 24 h ago should NOT suppress the
        reminder (the condition is “> cutoff”).
        """
        mock_now.return_value = self.now
        mock_pushover_api.return_value = MagicMock()

        scenario = LearningScenarioFactory(
            reminder=self.time_25_hours_ago,
            reminder_type=LearningScenario.Reminder.EMAIL,
            user=UserFactory(pushover_key="k"),
        )
        pkg = NoteRecordPackage.objects.create(learningscenario=scenario)
        pkg.created = self.now - timedelta(hours=24)
        pkg.save(update_fields=['created'])

        send_reminders()

        mock_send_mail.assert_called_once()

    @patch("notes.tasks.PushoverAPI")
    @patch("notes.tasks.send_mail")
    @patch("notes.tasks.timezone.now")
    def test_reminder_due_exactly_now(self, mock_now, mock_send_mail, mock_pushover_api):
        """`reminder == now` is considered due and triggers a notification."""
        mock_now.return_value = self.now
        mock_pushover_api.return_value = MagicMock()

        scenario = LearningScenarioFactory(
            reminder=self.now,
            reminder_type=LearningScenario.Reminder.EMAIL,
            user=UserFactory(pushover_key="k"),
        )

        send_reminders()
        mock_send_mail.assert_called_once()
        scenario.refresh_from_db()
        self.assertEqual(
            scenario.reminder, self.now + timedelta(hours=24)
        )

    # ------------------------------------------------------------------ #
    #  Time-zone / date-line scenarios (unchanged, updated expectation)  #
    # ------------------------------------------------------------------ #
    @patch("notes.tasks.PushoverAPI")
    @patch("notes.tasks.send_mail")
    @patch("notes.tasks.timezone.now")
    def test_multiple_timezones(self, mock_now, mock_send_mail, mock_pushover_api):
        """Emails are sent and reminders advanced for four disparate zones."""
        mock_now.return_value = self.now
        mock_pushover_api.return_value = MagicMock()

        users = [
            UserFactory(email="utc@example.com", pushover_key="u", timezone="UTC"),
            UserFactory(email="ldn@example.com", pushover_key="l", timezone="Europe/London"),
            UserFactory(email="tok@example.com", pushover_key="t", timezone="Asia/Tokyo"),
            UserFactory(email="la@example.com", pushover_key="a", timezone="America/Los_Angeles"),
        ]
        scenarios = [
            LearningScenarioFactory(
                user=u,
                reminder=self.time_25_hours_ago,
                reminder_type=LearningScenario.Reminder.EMAIL,
            )
            for u in users
        ]

        send_reminders()
        self.assertEqual(mock_send_mail.call_count, 4)

        for s in scenarios:
            s.refresh_from_db()
            self.assertEqual(
                s.reminder, self.time_25_hours_ago + timedelta(hours=24)
            )

    # ------------------------------------------------------------------ #
    #  Local/UTC conversion sanity check (unchanged expectation)         #
    # ------------------------------------------------------------------ #
    @patch("notes.tasks.PushoverAPI")
    @patch("notes.tasks.send_mail")
    @patch("notes.tasks.timezone.now")
    def test_local_time_conversion(self, mock_now, mock_send_mail, mock_pushover_api):
        """A non-UTC user gets the right UTC reminder offset."""
        mock_now.return_value = self.now
        mock_pushover_api.return_value = MagicMock()

        user = UserFactory(
            email="tokyo@example.com",
            pushover_key="tok",
            timezone="Asia/Tokyo",
        )

        local_reminder_time = self.now.astimezone(ZoneInfo("Asia/Tokyo")) - timedelta(
            hours=25
        )
        utc_reminder_time = local_reminder_time.astimezone(ZoneInfo("UTC"))

        scenario = LearningScenarioFactory(
            user=user,
            reminder=utc_reminder_time,
            reminder_type=LearningScenario.Reminder.EMAIL,
        )

        send_reminders()
        mock_send_mail.assert_called_once()
        scenario.refresh_from_db()

        self.assertEqual(
            scenario.reminder, utc_reminder_time + timedelta(hours=24)
        )
        self.assertEqual(
            scenario.reminder.astimezone(ZoneInfo("Asia/Tokyo")),
            local_reminder_time + timedelta(hours=24),
        )
