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


def _instrument_slug(name: str) -> str:
    """Create a slug for instrument matching (lowercase, hyphens between words)."""
    if not name:
        return ""
    s = str(name).strip().lower()
    # Normalize spaces and hyphens to single hyphens
    s = s.replace("_", "-").replace(" ", "-")
    while "--" in s:
        s = s.replace("--", "-")
    return s


# Precompute a slug -> canonical name map
INSTRUMENTS_BY_SLUG = { _instrument_slug(name): name for name in INSTRUMENTS.keys() }


def resolve_instrument(name_or_slug: str) -> str | None:
    """Resolve a user-provided instrument name/slug to the canonical name.
    Returns None if no match.
    """
    if not name_or_slug:
        return None
    # Exact match first
    if name_or_slug in INSTRUMENTS:
        return name_or_slug
    # Try by slug
    slug = _instrument_slug(name_or_slug)
    return INSTRUMENTS_BY_SLUG.get(slug)

def get_instrument_defaults() -> dict[str, dict[str, str | None]]:
    defaults: dict[str, dict[str, str | None]] = {}
    for name, data in INSTRUMENTS.items():
        slug = _instrument_slug(name)
        defaults[slug] = {"clefs": data.get("clefs"), "keys": data.get("common_keys")}
    return defaults

def get_instrument(name: str):
    """Get data for a specific instrument from the in-process snapshot."""
    canonical = resolve_instrument(name)
    if not canonical:
        return None
    return INSTRUMENTS.get(canonical)


def get_instrument_range(instrument: str, level: str):
    """Get the range of notes for an instrument at a specific level."""
    canonical = resolve_instrument(instrument)
    if not canonical:
        return None, None
    level = level.capitalize() if level else level

    instrument_data = INSTRUMENTS.get(canonical)
    if not instrument_data:
        return None, None

    level_data = instrument_data["skill_levels"].get(level)
    if not level_data:
        return None, None

    if "notes" in level_data and level_data["notes"]:
        notes = level_data["notes"].split(";")
        return notes[0], notes[-1]

    return level_data.get("lowest_note"), level_data.get("highest_note")


def get_fingerings(instrument: str):
    """Get the fingerings for an instrument."""
    canonical = resolve_instrument(instrument)
    if not canonical:
        return {}
    instrument_data = INSTRUMENTS.get(canonical)
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
