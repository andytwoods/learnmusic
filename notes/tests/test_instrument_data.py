"""
Tests for the instrument_data module and JSON file format.
"""
import json
import os
from django.test import TestCase
from django.conf import settings
from notes.instrument_data import load_instruments, get_instrument, get_instrument_range, get_fingerings


class TestInstrumentDataModule(TestCase):
    """Test the instrument_data module functions."""

    def test_load_instruments(self):
        """Test that instruments are loaded correctly."""
        instruments = load_instruments()
        self.assertTrue(len(instruments) > 0)
        self.assertIn('Trumpet', instruments)
        self.assertIn('Trombone', instruments)

    def test_get_instrument(self):
        """Test that get_instrument returns the correct instrument data."""
        trumpet = get_instrument('Trumpet')
        self.assertIsNotNone(trumpet)
        self.assertEqual(trumpet['name'], 'Trumpet')
        self.assertEqual(trumpet['ui_template'], 'trumpet.html')

        # Test with non-existent instrument
        self.assertIsNone(get_instrument('NonExistentInstrument'))

    def test_get_instrument_range(self):
        """Test that get_instrument_range returns the correct range."""
        # Test with Beginner level (notes)
        lowest, highest = get_instrument_range('Trumpet', 'Beginner')
        self.assertEqual(lowest, 'C 0 4')
        self.assertEqual(highest, 'F 0 5')

        # Test with Intermediate level (lowest_note, highest_note)
        lowest, highest = get_instrument_range('Trumpet', 'Intermediate')
        self.assertEqual(lowest, 'F 1 3')
        self.assertEqual(highest, 'C 0 5')

        # Test with non-existent instrument
        lowest, highest = get_instrument_range('NonExistentInstrument', 'Beginner')
        self.assertIsNone(lowest)
        self.assertIsNone(highest)

        # Test with non-existent level
        lowest, highest = get_instrument_range('Trumpet', 'NonExistentLevel')
        self.assertIsNone(lowest)
        self.assertIsNone(highest)

    def test_get_fingerings(self):
        """Test that get_fingerings returns the correct fingerings."""
        trumpet_fingerings = get_fingerings('Trumpet')
        self.assertTrue(len(trumpet_fingerings) > 0)
        self.assertIn('C/4', trumpet_fingerings)
        self.assertEqual(trumpet_fingerings['C/4'], [''])

        # Test with non-existent instrument
        self.assertEqual(get_fingerings('NonExistentInstrument'), {})


class TestInstrumentJSONFormat(TestCase):
    """Test that all instrument JSON files have the correct format."""

    def setUp(self):
        """Set up the test case."""
        # Get the path to the instruments directory
        self.instruments_dir = os.path.join(settings.STATIC_ROOT, 'instruments')
        if not os.path.exists(self.instruments_dir):
            self.instruments_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'instruments')

        # Get all JSON files in the instruments directory
        self.json_files = [f for f in os.listdir(self.instruments_dir) if f.endswith('.json')]

    def test_all_json_files_are_valid(self):
        """Test that all JSON files are valid JSON."""
        for filename in self.json_files:
            filepath = os.path.join(self.instruments_dir, filename)
            with self.subTest(filename=filename):
                with open(filepath) as f:
                    try:
                        json.load(f)
                    except json.JSONDecodeError as e:
                        self.fail(f"Invalid JSON in {filename}: {e}")

    def test_all_json_files_have_required_fields(self):
        """Test that all JSON files have the required fields."""
        required_fields = ['name', 'ui_template', 'clefs', 'common_keys', 'skill_levels', 'fingerings']

        for filename in self.json_files:
            filepath = os.path.join(self.instruments_dir, filename)
            with self.subTest(filename=filename):
                with open(filepath) as f:
                    data = json.load(f)
                    for field in required_fields:
                        self.assertIn(field, data, f"Missing required field '{field}' in {filename}")

    def test_skill_levels_have_required_fields(self):
        """Test that all skill levels have the required fields."""
        for filename in self.json_files:
            filepath = os.path.join(self.instruments_dir, filename)
            with self.subTest(filename=filename):
                with open(filepath) as f:
                    data = json.load(f)
                    skill_levels = data.get('skill_levels', {})

                    # Check that there are skill levels
                    self.assertTrue(len(skill_levels) > 0, f"No skill levels in {filename}")

                    # Check each skill level
                    for level_name, level_data in skill_levels.items():
                        # Each level must have either 'notes' or both 'lowest_note' and 'highest_note'
                        if 'notes' in level_data:
                            self.assertIsInstance(level_data['notes'], str,
                                                f"'notes' is not a string in {level_name} level in {filename}")

                            # Validate note format in 'notes' string
                            notes_list = level_data['notes'].split(';')
                            for note in notes_list:
                                parts = note.split(' ')
                                self.assertEqual(len(parts), 3, f"Invalid note format '{note}' in {filename} (expected 'NOTE ALTER OCTAVE')")
                                self.assertEqual(len(parts[0]), 1, f"Note name '{parts[0]}' must be single letter in {filename}")
                                self.assertTrue(parts[0] in 'ABCDEFG', f"Invalid note name '{parts[0]}' in {filename}")
                                try:
                                    int(parts[1])
                                    int(parts[2])
                                except ValueError:
                                    self.fail(f"Alter or Octave not an integer in '{note}' in {filename}")

                        else:
                            self.assertIn('lowest_note', level_data,
                                        f"Missing 'lowest_note' in {level_name} level in {filename}")
                            self.assertIn('highest_note', level_data,
                                        f"Missing 'highest_note' in {level_name} level in {filename}")

                            # Validate lowest/highest note format
                            for key in ['lowest_note', 'highest_note']:
                                note = level_data[key]
                                parts = note.split(' ')
                                self.assertEqual(len(parts), 3, f"Invalid {key} format '{note}' in {filename} (expected 'NOTE ALTER OCTAVE')")
                                self.assertEqual(len(parts[0]), 1, f"Note name '{parts[0]}' must be single letter in {filename}")
                                self.assertTrue(parts[0] in 'ABCDEFG', f"Invalid note name '{parts[0]}' in {filename}")
                                try:
                                    int(parts[1])
                                    int(parts[2])
                                except ValueError:
                                    self.fail(f"Alter or Octave not an integer in '{note}' in {filename}")

    def test_fingerings_format(self):
        """Test that fingerings have the correct format."""
        for filename in self.json_files:
            filepath = os.path.join(self.instruments_dir, filename)
            with self.subTest(filename=filename):
                with open(filepath) as f:
                    data = json.load(f)
                    fingerings = data.get('fingerings', {})

                    # Check that there are fingerings
                    self.assertTrue(len(fingerings) > 0, f"No fingerings in {filename}")

                    # Check each fingering
                    for note, fingering_list in fingerings.items():
                        self.assertIsInstance(fingering_list, list,
                                            f"Fingering for {note} is not a list in {filename}")
