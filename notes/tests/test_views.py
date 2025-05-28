from django.test import TestCase
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
