import json
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from notes.factories import LearningScenarioFactory, UserFactory
from notes.models import LearningScenario, NoteRecordPackage
from notes.tools import generate_notes


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



# Create your tests here.
class TestLearning(TestCase):

    def setUp(self):
        self.user = UserFactory()

    def test_learning(self):
        scenario = LearningScenarioFactory()
        scenario_id = scenario.id
        package1, serialised_notes1 = LearningScenario.progress_latest_serialised(scenario_id)

        package = NoteRecordPackage.objects.get(id=package1.id)
        serialised_notes1[0]['correct'].append(1)
        serialised_notes1[0]['reaction_time_log'].append(1000)
        package.process_answers(serialised_notes1)

        # let's check we get the updated package
        package2, serialised_notes2 = LearningScenario.progress_latest_serialised(scenario_id)
        self.assertEqual(package2.id, package.id)
        self.assertEqual(json.dumps(serialised_notes2), json.dumps(serialised_notes1))

        # we should get blank data when the package is made to be older than 24 hours
        with patch.object(NoteRecordPackage, 'older_than', return_value=True):
            package3, serialised_notes3 = LearningScenario.progress_latest_serialised(scenario_id)
            self.assertNotEqual(package3.id, package2.id)
            self.assertNotEqual(json.dumps(serialised_notes3), json.dumps(serialised_notes2))


class TestTools(TestCase):
    def test_generate_notes(self):
        start_note = 'A 1 4'
        end_note = 'G 1 4'

        notes = generate_notes(start_note, end_note, include_crazy_notes=True)
        self.assertEqual(len(notes), 18)

        start_note = 'F 1 3'
        end_note = 'C 0 6'
        notes = generate_notes(start_note, end_note, include_crazy_notes=True)

        start_note = 'F 1 3'
        end_note = 'C 0 5'
        notes = generate_notes(start_note, end_note, include_crazy_notes=True)
        self.assertListEqual(notes, ['F 1 3', 'G -1 3', 'G 0 3', 'G 1 3', 'A -1 3', 'A 0 3',
                                     'A 1 3', 'B -1 3', 'B 0 3', 'B 1 3', 'C -1 4', 'C 0 4',
                                     'C 1 4', 'D -1 4', 'D 0 4', 'D 1 4', 'E -1 4', 'E 0 4',
                                     'E 1 4', 'F -1 4', 'F 0 4', 'F 1 4', 'G -1 4', 'G 0 4',
                                     'G 1 4', 'A -1 4', 'A 0 4', 'A 1 4', 'B -1 4', 'B 0 4', 'B 1 4', 'C -1 5',
                                     'C 0 5'])

        start_note = 'F 1 3'
        end_note = 'B -1 5'
        notes = generate_notes(start_note, end_note, include_crazy_notes=True)
        self.assertListEqual(notes, ['F 1 3', 'G -1 3', 'G 0 3', 'G 1 3', 'A -1 3', 'A 0 3',
                                     'A 1 3', 'B -1 3', 'B 0 3', 'B 1 3', 'C -1 4', 'C 0 4',
                                     'C 1 4', 'D -1 4', 'D 0 4', 'D 1 4', 'E -1 4', 'E 0 4',
                                     'E 1 4', 'F -1 4', 'F 0 4', 'F 1 4', 'G -1 4', 'G 0 4',
                                     'G 1 4', 'A -1 4', 'A 0 4', 'A 1 4', 'B -1 4', 'B 0 4',
                                     'B 1 4', 'C -1 5', 'C 0 5', 'C 1 5', 'D -1 5', 'D 0 5',
                                     'D 1 5', 'E -1 5', 'E 0 5', 'E 1 5', 'F -1 5', 'F 0 5',
                                     'F 1 5', 'G -1 5', 'G 0 5', 'G 1 5', 'A -1 5', 'A 0 5',
                                     'A 1 5', 'B -1 5', 'B 0 5'])
