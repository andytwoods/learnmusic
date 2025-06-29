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

