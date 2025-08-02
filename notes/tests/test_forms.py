from datetime import datetime, timedelta
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

    def test_time_field_conversion(self):
        """Test that the TimeField is properly converted to a DateTimeField."""
        # Create form data with a time string
        form_data = {
            'instrument_name': 'Trumpet',
            'label': 'Test Label',
            'level': 'Beginner',  # Valid choice from LevelChoices
            'clef': 'Treble',     # Valid choice from ClefChoices
            'key': 'C',           # Valid choice from InstrumentKeys
            'transpose_key': 'BL', # Valid choice from transposing_choices (None)
            'octave_shift': 0,     # Default value
            'reminder': '14:30',   # Time in HH:MM format
            'reminder_type': 'AL'  # Valid choice from Reminder.choices (All notifications)
        }

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

