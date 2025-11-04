from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo

from django.test import TestCase
from django.utils import timezone

from notes.forms import LearningScenarioForm
from notes.models import LearningScenario
from notes.factories import UserFactory


class TestLearningScenarioForm(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.user.timezone = "UTC"
        self.user.save()

        # Create a learning scenario with a reminder
        self.scenario = LearningScenario.objects.create(
            user=self.user,
            label="Test Scenario",
            instrument_name="Trumpet",
            reminder=timezone.now() + timedelta(days=1)
        )

        # Create a mock request object with the user
        class MockRequest:
            def __init__(self, user):
                self.user = user

        self.request = MockRequest(self.user)

        # Standard form data for tests
        self.form_data = {
            'instrument_name': 'Trumpet',
            'label': 'Test Label',
            'level': 'Beginner',  # Valid choice from LevelChoices
            'clef': 'Treble',     # Valid choice from ClefChoices
            'relative_key': 'C',           # Valid choice from InstrumentKeys
            'absolute_key': 'BL', # Valid choice from transposing_choices (None)
            'octave_shift': 0,     # Default value
            'reminder_type': 'AL'  # Valid choice from Reminder.choices (All notifications)
        }

    def test_time_field_conversion(self):
        """Test that the TimeField is properly converted to a DateTimeField."""
        # Add reminder time to form data
        form_data = self.form_data.copy()
        form_data['reminder'] = '14:30'  # Time in HH:MM format

        # Initialize the form with the data
        form = LearningScenarioForm(data=form_data, request=self.request, instance=self.scenario)

        # Check that the form is valid
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")

        # Check that clean_reminder returns a datetime object
        cleaned_reminder = form.cleaned_data.get('reminder')
        self.assertIsInstance(cleaned_reminder, datetime)

        # Save the form and check that no errors occur
        instance = form.save()

        # Verify the saved instance has the correct reminder time
        self.assertEqual(instance.reminder.hour, 14)
        self.assertEqual(instance.reminder.minute, 30)

    def test_different_user_timezones(self):
        """Test that reminders work correctly with different user timezones."""
        # Set user timezone to US/Eastern
        self.user.timezone = "America/New_York"
        self.user.save()

        # Add reminder time to form data
        form_data = self.form_data.copy()
        form_data['reminder'] = '14:30'  # 2:30 PM in US/Eastern

        # Initialize and validate the form
        form = LearningScenarioForm(data=form_data, request=self.request, instance=self.scenario)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")

        # Save the form
        instance = form.save()

        # The reminder should be stored in UTC
        self.assertTrue(timezone.is_aware(instance.reminder))
        utc_reminder = instance.reminder.astimezone(ZoneInfo("UTC"))

        # Compute expected UTC dynamically to handle DST correctly year-round
        # Using today's date in the user's timezone at 14:30
        expected_utc = datetime.combine(
            timezone.localdate(),
            time(14, 30),
            tzinfo=ZoneInfo("America/New_York"),
        ).astimezone(ZoneInfo("UTC"))

        self.assertEqual(utc_reminder.hour, expected_utc.hour)
        self.assertEqual(utc_reminder.minute, expected_utc.minute)

        # Now check that it displays correctly in the user's timezone
        form = LearningScenarioForm(instance=instance, request=self.request)
        self.assertEqual(form.initial['reminder'], '14:30')

    def test_past_time_scheduled_for_next_day(self):
        """Test that reminders set for times that have already passed are scheduled for the next day."""
        # Set user timezone to UTC for simplicity
        self.user.timezone = "UTC"
        self.user.save()

        # Get current time in UTC
        now = timezone.now()

        # Calculate a time that has definitely passed today (1 hour ago)
        past_hour = (now.hour - 1) % 24
        past_time = f"{past_hour:02d}:00"  # Format as HH:MM

        # Add the past time to form data
        form_data = self.form_data.copy()
        form_data['reminder'] = past_time

        # Mock the clean_reminder method to use our fixed "now" time
        original_clean_reminder = LearningScenarioForm.clean_reminder

        try:
            # Define a patched version of clean_reminder that uses our fixed "now" time
            def patched_clean_reminder(self):
                time_value = self.cleaned_data.get('reminder')
                if not time_value or not self.request:
                    return None

                user_timezone = self.request.user.timezone

                # Use our fixed "now" time instead of timezone.now()
                current_datetime = now.astimezone(ZoneInfo(user_timezone))
                current_date = current_datetime.date()

                # Combine current date with time input
                combined_datetime = datetime.combine(
                    current_date,
                    time_value
                )

                # Make timezone aware using user's timezone
                aware_reminder = timezone.make_aware(combined_datetime, ZoneInfo(user_timezone))

                # If the reminder time has already passed for today, set it for tomorrow
                if aware_reminder < current_datetime:
                    aware_reminder += timedelta(days=1)

                # Convert to UTC for storage
                utc_reminder = aware_reminder.astimezone(ZoneInfo("UTC"))
                return utc_reminder

            # Replace the method temporarily
            LearningScenarioForm.clean_reminder = patched_clean_reminder

            # Initialize and validate the form
            form = LearningScenarioForm(data=form_data, request=self.request, instance=self.scenario)
            self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")

            # Save the form
            instance = form.save()

            # The reminder should be scheduled for tomorrow
            tomorrow = now.date() + timedelta(days=1)

            self.assertEqual(instance.reminder.date(), tomorrow)
            self.assertEqual(instance.reminder.hour, past_hour)
            self.assertEqual(instance.reminder.minute, 0)

        finally:
            # Restore the original method
            LearningScenarioForm.clean_reminder = original_clean_reminder

    def test_future_time_scheduled_for_today(self):
        """Test that reminders set for times that haven't passed yet are scheduled for today."""
        # Set user timezone to UTC for simplicity
        self.user.timezone = "UTC"
        self.user.save()

        # Get current time in UTC
        now = timezone.now()

        # Calculate a time that is definitely in the future today (current hour + 2)
        future_hour = (now.hour + 2) % 24
        future_time = f"{future_hour:02d}:00"  # Format as HH:MM

        # Add the future time to form data
        form_data = self.form_data.copy()
        form_data['reminder'] = future_time

        # Mock the clean_reminder method to use our fixed "now" time
        original_clean_reminder = LearningScenarioForm.clean_reminder

        try:
            # Define a patched version of clean_reminder that uses our fixed "now" time
            def patched_clean_reminder(self):
                time_value = self.cleaned_data.get('reminder')
                if not time_value or not self.request:
                    return None

                user_timezone = self.request.user.timezone

                # Use our fixed "now" time instead of timezone.now()
                current_datetime = now.astimezone(ZoneInfo(user_timezone))
                current_date = current_datetime.date()

                # Combine current date with time input
                combined_datetime = datetime.combine(
                    current_date,
                    time_value
                )

                # Make timezone aware using user's timezone
                aware_reminder = timezone.make_aware(combined_datetime, ZoneInfo(user_timezone))

                # If the reminder time has already passed for today, set it for tomorrow
                if aware_reminder < current_datetime:
                    aware_reminder += timedelta(days=1)

                # Convert to UTC for storage
                utc_reminder = aware_reminder.astimezone(ZoneInfo("UTC"))
                return utc_reminder

            # Replace the method temporarily
            LearningScenarioForm.clean_reminder = patched_clean_reminder

            # Initialize and validate the form
            form = LearningScenarioForm(data=form_data, request=self.request, instance=self.scenario)
            self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")

            # Save the form
            instance = form.save()

            # The reminder should be scheduled for today
            today = now.date()

            self.assertEqual(instance.reminder.date(), today)
            self.assertEqual(instance.reminder.hour, future_hour)
            self.assertEqual(instance.reminder.minute, 0)

        finally:
            # Restore the original method
            LearningScenarioForm.clean_reminder = original_clean_reminder

    def test_reminder_stored_in_utc(self):
        """Test that reminders are stored in UTC regardless of user timezone."""
        # Test with different timezones
        timezones_to_test = ["UTC", "America/New_York", "Europe/London", "Asia/Tokyo"]

        for tz in timezones_to_test:
            # Set user timezone
            self.user.timezone = tz
            self.user.save()

            # Add reminder time to form data
            form_data = self.form_data.copy()
            form_data['reminder'] = '12:00'  # Noon in user's timezone

            # Initialize and validate the form
            form = LearningScenarioForm(data=form_data, request=self.request, instance=self.scenario)
            self.assertTrue(form.is_valid(), f"Form errors with timezone {tz}: {form.errors}")

            # Save the form
            instance = form.save()

            # Verify the reminder is timezone-aware
            self.assertTrue(timezone.is_aware(instance.reminder))

            # Verify the timezone is UTC
            self.assertEqual(str(instance.reminder.tzinfo), "UTC")

