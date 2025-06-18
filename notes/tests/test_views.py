from datetime import datetime
from zoneinfo import ZoneInfo

from django.test import TestCase, Client
from django.urls import reverse

from notes.factories import LearningScenarioFactory, UserFactory
from notes.models import LearningScenario
from notes.views import common_context


class CommonContextTests(TestCase):
    def test_common_context(self):
        instrument_name = "Trumpet"
        clef = "treble"
        sound = True

        context = common_context(instrument_name, clef, sound)

        self.assertEqual(context["instrument"], instrument_name)
        self.assertEqual(context["clef"], clef.lower())


class TestPagesWork(TestCase):

    def setUp(self):
        self.user = UserFactory()
        self.login_page = reverse('account_login')

    def test_practice_try(self):
        for view in ['practice-sound-try', 'practice-try']:
            url = reverse(view, kwargs={'instrument': 'Trumpet', 'clef': 'Treble',
                                        'key': 'Bb', 'level': 'Beginner'})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

            for item in ['learningscenario_id', 'progress', 'key', 'level',
                         'sound', 'instrument', 'levels', 'instruments', 'clef', 'keys', 'clefs']:
                self.assertTrue(item in response.context)
                self.assertTrue(len(str(response.context[item])) > 0)

    def test_learningscenario_graph_try(self):
        url = reverse('learningscenario_graph_try',
                      kwargs={'instrument': 'Trumpet',
                              'level': 'Beginner'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        for item in ['progress', 'rt_per_sk']:
            self.assertTrue(item in response.context)
            self.assertTrue(len(str(response.context[item])) > 0)

    def test_learning_home(self):
        url = reverse('notes-home')
        response = self.client.get(url)
        self.assertIn(self.login_page, response['Location'])

        self.client.force_login(self.user)
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('learningscenarios' in response.context)

    def test_new_learning_scenario(self):
        url = reverse('new-learning-scenario')
        response = self.client.get(url)
        self.assertIn(self.login_page, response['Location'])

        self.client.force_login(self.user)
        self.assertFalse(LearningScenario.objects.all().exists())
        response = self.client.get(url)
        ls: LearningScenario = LearningScenario.objects.first()
        edit_scenario_url = reverse('edit-learning-scenario', kwargs={'pk': ls.id}) + '?new=true'
        self.assertEqual(response['Location'], edit_scenario_url)

    def test_edit_learning_scenario(self):

        ls: LearningScenario = LearningScenarioFactory(user=self.user)
        url = reverse('edit-learning-scenario', kwargs={'pk': ls.id})
        response = self.client.get(url)
        self.assertIn(self.login_page, response['Location'])

        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertTrue(response.status_code, 200)
        for item in ['form', 'learningscenario_pk', 'instruments_info', 'new']:
            self.assertTrue(item in response.context)


class TestReminderSettings(TestCase):
    """
    Tests for the reminder settings views, focusing on timezone conversion.
    """

    def setUp(self):
        self.client = Client()
        self.user = UserFactory()
        self.client.force_login(self.user)

    def test_reminder_settings_form_timezone_conversion(self):
        """
        Test that the reminder_settings_form view correctly converts UTC time to local time.
        """
        # Set up a user with a reminder time in UTC
        profile = self.user.profile
        utc_reminder_time = "14:00"  # 2 PM UTC
        profile.reminder_time = utc_reminder_time
        profile.timezone = "America/New_York"  # UTC-5 or UTC-4 depending on DST
        profile.save()

        # Get the reminder settings form
        response = self.client.get(reverse('reminder-settings-form'))
        self.assertEqual(response.status_code, 200)

        # Check that the reminder time in the form is converted to the user's local timezone
        # The exact time depends on whether DST is in effect, so we'll check that it's different from UTC
        form_reminder_time = response.context['reminder_time']
        self.assertNotEqual(form_reminder_time, utc_reminder_time)

        # Parse the times to verify the conversion is correct
        utc_hour, utc_minute = map(int, utc_reminder_time.split(':'))
        local_hour, local_minute = map(int, form_reminder_time.split(':'))

        # Create datetime objects for comparison
        utc_dt = datetime.now(ZoneInfo("UTC")).replace(hour=utc_hour, minute=utc_minute)
        local_dt = utc_dt.astimezone(ZoneInfo("America/New_York"))

        # Check that the local hour matches what we expect
        expected_local_hour = local_dt.hour
        expected_local_minute = local_dt.minute
        self.assertEqual(local_hour, expected_local_hour)
        self.assertEqual(local_minute, expected_local_minute)

    def test_reminder_settings_form_multiple_timezones(self):
        """
        Test that the reminder_settings_form view correctly converts UTC time to various local timezones.
        """
        # Test with multiple different timezones
        timezones_to_test = [
            "Europe/London",      # UTC+0/+1
            "Europe/Paris",       # UTC+1/+2
            "Asia/Tokyo",         # UTC+9
            "Australia/Sydney",   # UTC+10/+11
            "Pacific/Auckland",   # UTC+12/+13
            "America/Los_Angeles" # UTC-8/-7
        ]

        utc_reminder_time = "12:00"  # Noon UTC

        for tz_name in timezones_to_test:
            # Set up the user with the current timezone
            profile = self.user.profile
            profile.reminder_time = utc_reminder_time
            profile.timezone = tz_name
            profile.save()

            # Get the reminder settings form
            response = self.client.get(reverse('reminder-settings-form'))
            self.assertEqual(response.status_code, 200)

            # Check that the reminder time in the form is converted to the user's local timezone
            form_reminder_time = response.context['reminder_time']

            # Parse the times to verify the conversion is correct
            utc_hour, utc_minute = map(int, utc_reminder_time.split(':'))
            local_hour, local_minute = map(int, form_reminder_time.split(':'))

            # Create datetime objects for comparison
            utc_dt = datetime.now(ZoneInfo("UTC")).replace(hour=utc_hour, minute=utc_minute)
            local_dt = utc_dt.astimezone(ZoneInfo(tz_name))

            # Check that the local hour matches what we expect
            expected_local_hour = local_dt.hour
            expected_local_minute = local_dt.minute
            self.assertEqual(local_hour, expected_local_hour, f"Failed for timezone {tz_name}")
            self.assertEqual(local_minute, expected_local_minute, f"Failed for timezone {tz_name}")

    def test_reminder_settings_submit_timezone_conversion(self):
        """
        Test that the reminder_settings_submit view correctly converts local time to UTC.
        """
        # Submit a reminder time in a non-UTC timezone
        local_reminder_time = "09:00"  # 9 AM local time
        user_timezone = "America/New_York"  # UTC-5 or UTC-4 depending on DST

        response = self.client.post(reverse('reminder-settings-submit'), {
            'reminder_time': local_reminder_time,
            'timezone': user_timezone
        })
        self.assertEqual(response.status_code, 200)

        # Check that the reminder time was saved in UTC
        self.user.refresh_from_db()
        utc_reminder_time = self.user.profile.reminder_time

        # Parse the times to verify the conversion is correct
        local_hour, local_minute = map(int, local_reminder_time.split(':'))
        utc_hour, utc_minute = map(int, utc_reminder_time.split(':'))

        # Create datetime objects for comparison
        local_dt = datetime.now(ZoneInfo(user_timezone)).replace(hour=local_hour, minute=local_minute)
        utc_dt = local_dt.astimezone(ZoneInfo("UTC"))

        # Check that the UTC hour matches what we expect
        expected_utc_hour = utc_dt.hour
        expected_utc_minute = utc_dt.minute
        self.assertEqual(utc_hour, expected_utc_hour)
        self.assertEqual(utc_minute, expected_utc_minute)

    def test_reminder_settings_submit_multiple_timezones(self):
        """
        Test that the reminder_settings_submit view correctly converts local time to UTC for various timezones.
        """
        # Test with multiple different timezones
        timezones_to_test = [
            "Europe/London",      # UTC+0/+1
            "Europe/Paris",       # UTC+1/+2
            "Asia/Tokyo",         # UTC+9
            "Australia/Sydney",   # UTC+10/+11
            "Pacific/Auckland",   # UTC+12/+13
            "America/Los_Angeles" # UTC-8/-7
        ]

        local_reminder_time = "15:00"  # 3 PM local time

        for tz_name in timezones_to_test:
            # Submit a reminder time in the current timezone
            response = self.client.post(reverse('reminder-settings-submit'), {
                'reminder_time': local_reminder_time,
                'timezone': tz_name
            })
            self.assertEqual(response.status_code, 200)

            # Check that the reminder time was saved in UTC
            self.user.refresh_from_db()
            utc_reminder_time = self.user.profile.reminder_time

            # Parse the times to verify the conversion is correct
            local_hour, local_minute = map(int, local_reminder_time.split(':'))
            utc_hour, utc_minute = map(int, utc_reminder_time.split(':'))

            # Create datetime objects for comparison
            local_dt = datetime.now(ZoneInfo(tz_name)).replace(hour=local_hour, minute=local_minute)
            utc_dt = local_dt.astimezone(ZoneInfo("UTC"))

            # Check that the UTC hour matches what we expect
            expected_utc_hour = utc_dt.hour
            expected_utc_minute = utc_dt.minute
            self.assertEqual(utc_hour, expected_utc_hour, f"Failed for timezone {tz_name}")
            self.assertEqual(utc_minute, expected_utc_minute, f"Failed for timezone {tz_name}")

    def test_disabled_reminders(self):
        """
        Test that the 'DISABLED' value is preserved and not converted.
        """
        # Submit a request to disable reminders
        response = self.client.post(reverse('reminder-settings-submit'), {
            'remove_reminders': 'true'
        })
        self.assertEqual(response.status_code, 200)

        # Check that the reminder time was set to DISABLED
        self.user.refresh_from_db()
        self.assertEqual(self.user.profile.reminder_time, "DISABLED")
