"""
Module for loading and processing instrument data from JSON files.
"""
import json
import os
from django.conf import settings


def load_instruments():
    """Load all instrument data from JSON files."""
    instruments_data = {}
    instruments_dir = os.path.join(settings.STATIC_ROOT, 'instruments')

    # If STATIC_ROOT is not set or the directory doesn't exist, use the static directory in the app
    if not os.path.exists(instruments_dir):
        instruments_dir = os.path.join(os.path.dirname(__file__), 'static', 'instruments')

    for filename in os.listdir(instruments_dir):
        if filename.endswith('.json'):
            with open(os.path.join(instruments_dir, filename)) as f:
                instrument_data = json.load(f)
                instruments_data[instrument_data['name']] = instrument_data

    return instruments_data


# Load instruments once at module level
INSTRUMENTS = load_instruments()


def get_instrument(name):
    """Get data for a specific instrument."""
    return INSTRUMENTS.get(name)


def get_instrument_range(instrument, level):
    """Get the range of notes for an instrument at a specific level."""
    instrument_data = get_instrument(instrument)
    if not instrument_data:
        return None, None

    level_data = instrument_data['skill_levels'].get(level)
    if not level_data:
        return None, None

    if 'notes' in level_data:
        notes = level_data['notes'].split(';')
        return notes[0], notes[-1]

    return level_data.get('lowest_note'), level_data.get('highest_note')


def get_fingerings(instrument):
    """Get the fingerings for an instrument."""
    instrument_data = get_instrument(instrument)
    if not instrument_data:
        return {}

    return instrument_data.get('fingerings', {})


# For backward compatibility with the existing code
instruments = {}
instrument_infos = {}

for name, data in INSTRUMENTS.items():
    # Create instruments dictionary structure
    instruments[name] = {}
    for level, level_data in data['skill_levels'].items():
        instruments[name][level] = level_data

    # Create instrument_infos dictionary structure
    instrument_infos[name] = {
        'answer_template': data['ui_template'],
        'answers': f"{name.lower()}.json",
        'clef': data['clefs'],
        'common_keys': data['common_keys'],
    }
