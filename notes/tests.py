from django.test import TestCase

from notes.factories import NoteFactory, LearningScenarioFactory
from notes.models import Note, LearningScenario
from notes.tools import generate_notes, generate_notes_from_str


# Create your tests here.

class TestTools(TestCase):
    def test_generate_notes(self):
        start_note: Note = NoteFactory(note='A', alter=1, octave=4)
        end_note: Note = NoteFactory(
            note='G', alter=1, octave=4
        )
        notes = generate_notes(start_note, end_note, include_crazy_notes=True)
        self.assertEqual(len(notes), 18)

        start_note = NoteFactory(note='F', alter=1, octave=3)
        end_note = NoteFactory(note='C', alter=0, octave=6)
        notes = generate_notes(start_note, end_note, include_crazy_notes=True)

        start_note = NoteFactory(note='F', alter=1, octave=3)
        end_note = NoteFactory(note='C', alter=0, octave=5)
        notes = generate_notes(start_note, end_note, include_crazy_notes=True, json=True)
        self.assertListEqual(notes, ['F 1 3', 'G -1 3', 'G 0 3', 'G 1 3', 'A -1 3', 'A 0 3',
                                     'A 1 3', 'B -1 3', 'B 0 3', 'B 1 3', 'C -1 4', 'C 0 4',
                                     'C 1 4', 'D -1 4', 'D 0 4', 'D 1 4', 'E -1 4', 'E 0 4',
                                     'E 1 4', 'F -1 4', 'F 0 4', 'F 1 4', 'G -1 4', 'G 0 4',
                                     'G 1 4', 'A -1 4', 'A 0 4', 'A 1 4', 'B -1 4', 'B 0 4', 'B 1 4', 'C -1 5',
                                     'C 0 5'] )

        start_note = NoteFactory(note='F', alter=1, octave=3)
        end_note = NoteFactory(note='B', alter=-1, octave=5)
        notes = generate_notes(start_note, end_note, include_crazy_notes=True, json=True)
        self.assertListEqual(notes, ['F 1 3', 'G -1 3', 'G 0 3', 'G 1 3', 'A -1 3', 'A 0 3',
                                     'A 1 3', 'B -1 3', 'B 0 3', 'B 1 3', 'C -1 4', 'C 0 4',
                                     'C 1 4', 'D -1 4', 'D 0 4', 'D 1 4', 'E -1 4', 'E 0 4',
                                     'E 1 4', 'F -1 4', 'F 0 4', 'F 1 4', 'G -1 4', 'G 0 4',
                                     'G 1 4', 'A -1 4', 'A 0 4', 'A 1 4', 'B -1 4', 'B 0 4',
                                     'B 1 4', 'C -1 5', 'C 0 5', 'C 1 5', 'D -1 5', 'D 0 5',
                                     'D 1 5', 'E -1 5', 'E 0 5', 'E 1 5', 'F -1 5', 'F 0 5',
                                     'F 1 5', 'G -1 5', 'G 0 5', 'G 1 5', 'A -1 5', 'A 0 5',
                                     'A 1 5', 'B -1 5', 'B 0 5']
)


    def test_generate_notes_from_str(self):
        notes_str = 'C 0 4;D 0 4;E 0 4;F 0 4;G 0 4;A 0 4;Bb -1 4;B 0 4;C 0 5;D 0 5;E 0 5;F 0 5;G 0 5'
        notes = generate_notes_from_str(notes_str)
        self.assertEqual(len(notes), 13)

class TestModels(TestCase):
    def test_progress_latest_serialised(self):
        scenario: LearningScenario = LearningScenarioFactory()

