"""
Tests to ensure all note strings in instrument JSON files serialise without error.

This test recursively scans all JSON files under notes/static/instruments and finds any
values whose keys start with one of the following prefixes: "notes", "lowest_note",
"highest_note". For every such value that is a string (and not empty), the test passes
it to notes.tools.serialise_notes. Any exception means the JSON data is malformed.
"""
import json
import os
from typing import Any

from django.conf import settings
from django.test import TestCase

from notes.tools import serialise_notes


KEY_PREFIXES = ("notes", "lowest_note", "highest_note")


class TestNotesSerialisationFromJSON(TestCase):
    def setUp(self):
        # Resolve instruments directory similarly to instrument_data.py
        instruments_dir = os.path.join(settings.STATIC_ROOT, "instruments")
        if not os.path.exists(instruments_dir):
            instruments_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "instruments")
        self.instruments_dir = instruments_dir

        # Collect all JSON files
        self.json_files = [f for f in os.listdir(self.instruments_dir) if f.endswith(".json")]
        self.assertTrue(self.json_files, "No instrument JSON files found")

    def _traverse_and_test(self, obj: Any, filename: str, path: str = "$"):
        if isinstance(obj, dict):
            for k, v in obj.items():
                # Recurse first to ensure deep coverage
                self._traverse_and_test(v, filename, f"{path}.{k}")
                # If key starts with our prefixes, validate the value
                if isinstance(k, str) and k.startswith(KEY_PREFIXES):
                    # Only process string values; None or other types are not serialisable by design
                    if isinstance(v, str) and v:
                        try:
                            serialise_notes(v)
                        except Exception as e:  # noqa: BLE001 - we want to surface anything here
                            self.fail(
                                f"Failed to serialise value at {filename}:{path}.{k} -> {v!r}. Error: {e}"
                            )
        elif isinstance(obj, list):
            for idx, item in enumerate(obj):
                self._traverse_and_test(item, filename, f"{path}[{idx}]")
        else:
            # Primitive types (str/int/None/etc.) are handled at dict key level only
            return

    def test_all_note_strings_serialise(self):
        for filename in self.json_files:
            filepath = os.path.join(self.instruments_dir, filename)
            with self.subTest(filename=filename):
                with open(filepath) as f:
                    data = json.load(f)
                self._traverse_and_test(data, filename)
