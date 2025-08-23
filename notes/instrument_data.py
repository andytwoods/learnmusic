"""
Module for loading and processing instrument data from JSON files.
"""
import json
import os

from django.conf import settings


def _get_instruments_dir() -> str:
    """Resolve the directory where instrument JSON files live."""
    instruments_dir = os.path.join(settings.STATIC_ROOT, "instruments")
    # If STATIC_ROOT is not set or the directory doesn't exist, use the app's static directory
    if not os.path.exists(instruments_dir):
        instruments_dir = os.path.join(os.path.dirname(__file__), "static", "instruments")
    return instruments_dir


def load_instruments():
    """Load all instrument data from JSON files (no Django caching)."""
    instruments_dir = _get_instruments_dir()

    instruments_data = {}
    for filename in os.listdir(instruments_dir):
        if filename.endswith(".json"):
            with open(os.path.join(instruments_dir, filename)) as f:
                instrument_data = json.load(f)
                instruments_data[instrument_data["name"]] = instrument_data
    return instruments_data


# Load instruments once at module level (per-process snapshot)
INSTRUMENTS = load_instruments()


def get_instrument(name: str):
    """Get data for a specific instrument from the in-process snapshot."""
    # Ensure name is properly capitalized
    name = name.capitalize() if name else name
    return INSTRUMENTS.get(name)


def get_instrument_range(instrument: str, level: str):
    """Get the range of notes for an instrument at a specific level."""
    # Ensure instrument and level are properly capitalized
    instrument = instrument.capitalize() if instrument else instrument
    level = level.capitalize() if level else level

    instrument_data = get_instrument(instrument)
    if not instrument_data:
        return None, None

    level_data = instrument_data["skill_levels"].get(level)
    if not level_data:
        return None, None

    if "notes" in level_data:
        notes = level_data["notes"].split(";")
        return notes[0], notes[-1]

    return level_data.get("lowest_note"), level_data.get("highest_note")


def get_fingerings(instrument: str):
    """Get the fingerings for an instrument."""
    # Ensure instrument is properly capitalized
    instrument = instrument.capitalize() if instrument else instrument

    instrument_data = get_instrument(instrument)
    if not instrument_data:
        return {}

    fingerings = instrument_data.get("fingerings", {})
    return dict(fingerings)


# For backward compatibility with the existing code
instruments = {}
instrument_infos = {}

for name, data in INSTRUMENTS.items():
    # Create instruments dictionary structure
    instruments[name] = {}
    for level, level_data in data["skill_levels"].items():
        instruments[name][level] = level_data

    # Create instrument_infos dictionary structure
    instrument_infos[name] = {
        "answer_template": data["ui_template"],
        "answers": f"{name.lower()}.json",
        "clef": data["clefs"],
        "common_keys": data["common_keys"],
    }
