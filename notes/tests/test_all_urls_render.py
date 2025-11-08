import json

from django.test import TestCase
from django.urls import reverse

from notes.factories import LearningScenarioFactory, UserFactory
from notes.models import LearningScenario


class TestAllNotesUrlsRender(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_login(self.user)

    def test_test_js_renders(self):
        resp = self.client.get(reverse("test-js"))
        self.assertEqual(resp.status_code, 200)

    def test_notes_home_requires_login_then_renders(self):
        self.client.logout()
        login_url = reverse("account_login")
        resp = self.client.get(reverse("notes-home"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(login_url, resp["Location"])
        self.client.force_login(self.user)
        resp = self.client.get(reverse("notes-home"))
        self.assertEqual(resp.status_code, 200)


    def test_new_and_edit_learningscenario_flow(self):
        # new -> redirect to edit (already covered elsewhere but keep simple check here)
        self.client.logout()
        resp = self.client.get(reverse("new-learning-scenario"))
        self.assertEqual(resp.status_code, 302)
        self.client.force_login(self.user)
        resp = self.client.get(reverse("new-learning-scenario"))
        self.assertEqual(resp.status_code, 302)
        # Follow redirect target exists
        ls = LearningScenario.objects.first()
        self.assertIsNotNone(ls)
        edit_url = reverse("edit-learning-scenario", kwargs={"pk": ls.id})
        resp = self.client.get(edit_url)
        self.assertEqual(resp.status_code, 200)

    def test_edit_learningscenario_notes_renders(self):
        ls = LearningScenarioFactory(user=self.user)
        url = reverse("edit-learning-scenario-notes", kwargs={"pk": ls.id})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("notes", resp.context)
        self.assertIn("all_notes", resp.context)

    def test_practice_and_sound_renders(self):
        ls = LearningScenarioFactory(user=self.user)
        # practice
        resp = self.client.get(reverse("practice", kwargs={"learningscenario_id": ls.id}))
        self.assertEqual(resp.status_code, 200)
        # practice-sound
        resp = self.client.get(reverse("practice-sound", kwargs={"learningscenario_id": ls.id}))
        self.assertEqual(resp.status_code, 200)


    def test_practice_data_post(self):
        ls = LearningScenarioFactory(user=self.user)
        # Ensure a package exists and get its id
        from notes.models import LearningScenario as LS
        package, _progress = LS.progress_latest_serialised(ls.id)
        url = reverse("practice-data", kwargs={"package_id": package.id})
        payload = {
            "note": "C",
            "alter": "0",
            "octave": "4",
            "reaction_time": 800,
            "correct": True,
        }
        resp = self.client.post(url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json().get("success"), True)

    def test_progress_data_view_json(self):
        # No scenario needed; endpoint returns empty aggregates OK
        resp = self.client.get(reverse("progress_data", kwargs={"learningscenario_id": 999999}))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("over_time", data)
        self.assertIn("by_note", data)

    def test_practice_demo_redirects(self):
        resp = self.client.get(reverse("practice-demo"))
        self.assertEqual(resp.status_code, 302)

    def test_practice_try_variants_render(self):
        # without absolute pitch
        url = reverse(
            "practice-try-sigs",
            kwargs={
                "instrument": "Trumpet",
                "clef": "Treble",
                "key": "Bb",
                "level": "Beginner",
                "octave": 0,
                "signatures": "0",
            },
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        # with absolute pitch
        url = reverse(
            "practice-try-sigs-abs",
            kwargs={
                "instrument": "Trumpet",
                "clef": "Treble",
                "key": "Bb",
                "absolute_pitch": "Bb",
                "level": "Beginner",
                "octave": 0,
                "signatures": "0",
            },
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_manifest_routes_return_json(self):
        # without absolute pitch
        url = reverse(
            "practice-try-manifest-sigs",
            kwargs={
                "instrument": "Trumpet",
                "clef": "Treble",
                "key": "Bb",
                "level": "Beginner",
                "octave": 0,
                "signatures": "0",
            },
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("name", resp.json())

        # with absolute pitch
        url = reverse(
            "practice-try-manifest-sigs-abs",
            kwargs={
                "instrument": "Trumpet",
                "clef": "Treble",
                "key": "Bb",
                "absolute_pitch": "Bb",
                "level": "Beginner",
                "octave": 0,
                "signatures": "0",
            },
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("name", resp.json())


    def test_pushover_callback_redirects(self):
        self.client.logout()
        resp = self.client.get(reverse("pushover_callback"))
        self.assertEqual(resp.status_code, 302)
        self.client.force_login(self.user)
        resp = self.client.get(reverse("pushover_callback"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("notes-home"), resp["Location"])


