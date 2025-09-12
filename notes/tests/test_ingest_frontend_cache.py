from django.test import TestCase
from django.contrib.auth import get_user_model

from notes.models import LearningScenario, NoteRecord, NoteRecordPackage
from notes.instrument_data import INSTRUMENTS


class TestIngestFrontendCache(TestCase):
    def setUp(self):
        User = get_user_model()
        # Custom user model uses email as the unique identifier
        self.user = User.objects.create_user(email="t@example.com", password="pw")

        # Pick a valid instrument and defaults from loaded instrument data
        self.instrument = next(iter(INSTRUMENTS.keys()))
        data = INSTRUMENTS[self.instrument]
        self.level = "Beginner"
        # Choose first available clef and key
        self.clef = (data.get("clefs") or ["Treble"])[0]
        self.key = (data.get("common_keys") or ["C"])[0]

        self.info = {
            "instrument": self.instrument,
            "level": self.level,
            "clef": self.clef,
            "relative_key": self.key,
            # Provide as string to verify int casting occurs in ingest_frontend_cache
            "shifted_octave": "1",
            # Use blank transpose sentinel; the model accepts this value
            "absolute_key": "BL",
        }

        # History with two entries -> creates three NoteRecord rows total (2 + 1)
        self.notes_history_list = [
            {
                "alter": "0",
                "note": "C",
                "octave": "4",
                "reaction_time_log": [500, 450],
                "correct": [True, False],
            },
            {
                "alter": "1",
                "note": "F",
                "octave": "4",
                "reaction_time_log": [700],
                "correct": [True],
            },
        ]

    def test_creates_learningscenario_package_and_records(self):
        # Act
        ls, pkg = LearningScenario.ingest_frontend_cache(self.user, self.info, self.notes_history_list)

        # Assert LearningScenario fields
        self.assertEqual(ls.user, self.user)
        self.assertEqual(ls.instrument_name, self.instrument)
        self.assertEqual(ls.level, self.level)
        self.assertEqual(ls.clef, self.clef)
        self.assertEqual(ls.relative_key, self.key)
        self.assertEqual(ls.octave_shift, 1)  # ensure string was cast to int
        self.assertEqual(ls.absolute_key, "BL")

        # Assert NoteRecordPackage/log
        self.assertIsInstance(pkg, NoteRecordPackage)
        self.assertEqual(pkg.learningscenario, ls)
        self.assertEqual(pkg.log, self.notes_history_list)

        # Assert NoteRecord rows created from logs
        expected_records = sum(min(len(x.get("reaction_time_log", [])), len(x.get("correct", []))) for x in self.notes_history_list)
        self.assertEqual(NoteRecord.objects.filter(learningscenario=ls).count(), expected_records)

        # Spot-check first record content
        first = NoteRecord.objects.filter(learningscenario=ls, note="C", alter="0", octave="4").order_by("created").first()
        self.assertIsNotNone(first)
        self.assertIn(first.reaction_time, [500, 450])
        self.assertIn(first.correct, [True, False])

    def test_idempotent_get_or_create_same_ls_new_package(self):
        # First ingest
        ls1, pkg1 = LearningScenario.ingest_frontend_cache(self.user, self.info, self.notes_history_list)
        # Second ingest with same identifying info
        ls2, pkg2 = LearningScenario.ingest_frontend_cache(self.user, self.info, self.notes_history_list)

        self.assertEqual(ls1.id, ls2.id, "Expected same LearningScenario to be reused for identical info")
        self.assertNotEqual(pkg1.id, pkg2.id, "Expected a new NoteRecordPackage to be created each ingest")

    def test_non_list_history_is_logged_without_creating_records(self):
        payload = {"some": "data"}
        ls, pkg = LearningScenario.ingest_frontend_cache(self.user, self.info, payload)

        self.assertEqual(pkg.log, payload)
        self.assertEqual(NoteRecord.objects.filter(learningscenario=ls).count(), 0)
