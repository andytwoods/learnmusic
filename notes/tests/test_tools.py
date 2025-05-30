
from django.test import TestCase
from notes.tools import serialise_note, serialise_notes, generate_notes, sort_notes, compile_notes_per_skilllevel, \
    generate_serialised_notes, get_instrument_range

class TestTools(TestCase):
    def test_compile_notes_per_skilllevel(self):
        notes = [{'note': 'C', 'octave': '4', 'alter': '0'}]
        compiled = compile_notes_per_skilllevel(notes)
        self.assertIn('Beginner', compiled)
        self.assertIn('Intermediate', compiled)
        self.assertIn('Advanced', compiled)

    def test_serialise_notes(self):
        notes_str = "C 0 4;D 0 4"
        serialised = serialise_notes(notes_str)
        self.assertEqual(len(serialised), 2)
        self.assertEqual(serialised[0]['note'], 'C')

    def test_serialise_note(self):
        note_str = "C 0 4"
        serialised = serialise_note(note_str)
        self.assertEqual(serialised['note'], 'C')
        self.assertEqual(serialised['octave'], '4')

    def test_generate_serialised_notes(self):
        # Mock instruments data for testing
        instruments = {
            'piano': {
                'beginner': {
                    'lowest_note': 'C 0 4',
                    'highest_note': 'C 0 5'
                }
            }
        }
        notes = generate_serialised_notes('Trumpet', 'Beginner')
        self.assertTrue(len(notes) > 0)

    def test_get_instrument_range(self):
        # Mock instruments data for testing
        instruments = {
            'piano': {
                'beginner': {
                    'lowest_note': 'C 0 4',
                    'highest_note': 'C 0 5'
                }
            }
        }

        lowest, highest = get_instrument_range('Trumpet', 'Beginner')
        self.assertEqual(lowest, 'C 0 4')
        self.assertEqual(highest, 'F 0 5')

    def test_sort_notes(self):
        notes = {
            "C4": [],
            "D4": [],
            "B3": [],
            "A#3": []
        }
        sorted_notes = sort_notes(notes)
        self.assertEqual(list(sorted_notes.keys()), ["A#3", "B3", "C4", "D4"])
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


class TestToolsFunctions(TestCase):
    def setUp(self):
        self.example_note_records = [
            'C 0 4', 'D 0 4', 'E 0 4', 'F 0 4', 'G 0 4', 'A 0 4',
            'B -1 4', 'B 0 4', 'C 0 5', 'A 0 3', 'B 0 3', 'F 1 4',
            'D 0 5', 'E 0 5', 'F 0 5'
        ]

    def test_serialise_note_with_example_data(self):
        """Test serialise_note function with example data from the issue description."""
        # Test with a natural note
        note_str = 'C 0 4'
        result = serialise_note(note_str)

        self.assertEqual(result['note'], 'C')
        self.assertEqual(result['octave'], '4')
        self.assertEqual(result['alter'], '0')
        self.assertEqual(result['reaction_time'], '')
        self.assertEqual(result['n'], 0)
        self.assertEqual(result['reaction_time_log'], [])
        self.assertEqual(result['correct'], [])

        # Test with a flat note
        note_str = 'B -1 4'
        result = serialise_note(note_str)

        self.assertEqual(result['note'], 'B')
        self.assertEqual(result['octave'], '4')
        self.assertEqual(result['alter'], '-1')

        # Test with a sharp note
        note_str = 'F 1 4'
        result = serialise_note(note_str)

        self.assertEqual(result['note'], 'F')
        self.assertEqual(result['octave'], '4')
        self.assertEqual(result['alter'], '1')

    def test_serialise_notes_with_example_data(self):
        """Test serialise_notes function with example data."""
        notes_str = 'C 0 4;D 0 4;E 0 4'
        results = serialise_notes(notes_str)

        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]['note'], 'C')
        self.assertEqual(results[1]['note'], 'D')
        self.assertEqual(results[2]['note'], 'E')

    def test_generate_notes_with_example_range(self):
        """Test generate_notes function with a range from the example data."""
        # Generate notes from C4 to F5 (covering most of the example range)
        lowest_note = 'C 0 4'
        highest_note = 'F 0 5'

        notes = generate_notes(lowest_note, highest_note)

        # The generate_notes function returns compiled[1:-1], which excludes the first and last elements
        # So we need to check for notes that would be in the middle of the range
        middle_notes = ['D 0 4', 'E 0 4', 'F 0 4', 'G 0 4', 'A 0 4', 'B -1 4', 'B 0 4', 'C 0 5', 'D 0 5', 'E 0 5']

        for note in middle_notes:
            # Skip sharps as they might be excluded by include_crazy_notes=False
            note_parts = note.split(' ')
            if note_parts[1] == '1':  # Skip sharps
                continue

            self.assertIn(note, notes, f"Note {note} should be in the generated range")

        # Verify some notes are in the expected range
        self.assertTrue(any(note.startswith('D') and note.endswith('4') for note in notes))
        self.assertTrue(any(note.startswith('E') and note.endswith('5') for note in notes))

    def test_serialise_note_format_consistency(self):
        """Test that serialise_note produces the expected format for progress tracking."""
        # Test all example notes
        for note_str in self.example_note_records:
            result = serialise_note(note_str)

            # Check all required fields are present
            self.assertIn('note', result)
            self.assertIn('octave', result)
            self.assertIn('alter', result)
            self.assertIn('reaction_time', result)
            self.assertIn('n', result)
            self.assertIn('reaction_time_log', result)
            self.assertIn('correct', result)

            # Check the types of the fields
            self.assertIsInstance(result['note'], str)
            self.assertIsInstance(result['octave'], str)
            self.assertIsInstance(result['alter'], str)
            self.assertIsInstance(result['reaction_time'], str)
            self.assertIsInstance(result['n'], int)
            self.assertIsInstance(result['reaction_time_log'], list)
            self.assertIsInstance(result['correct'], list)
