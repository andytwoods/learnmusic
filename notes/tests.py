from django.test import TestCase

from notes.factories import NoteFactory, LearningScenarioFactory
from notes.models import Note, LearningScenario
from notes.tools import generate_notes


# Create your tests here.

class TestTools(TestCase):
    def test_generate_notes(self):
        start_note: Note = NoteFactory(note='A', alter=1, octave=4)
        end_note: Note = NoteFactory(
            note='G', alter=1, octave=4
        )
        notes = generate_notes(start_note, end_note, include_crazy_notes=True)
        self.assertEqual(len(notes), 19)

class TestModels(TestCase):
    def test_progress_latest_serialised(self):
        scenario: LearningScenario = LearningScenarioFactory()

