from django.test import TestCase

from notes.views import common_context


class CommonContextTests(TestCase):
    def test_common_context(self):
        instrument_name = "Piano"
        clef = "treble"
        sound = True

        context = common_context(instrument_name, clef, sound)

        self.assertEqual(context["instrument_name"], instrument_name)
        self.assertEqual(context["clef"], clef)
        self.assertEqual(context["sound"], sound)
