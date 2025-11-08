import random

from notes.instrument_data import instruments, resolve_instrument

notes = [
    "A♭ / G♯",
    "A",
    "A♯ / B♭",
    "B / C♭",
    "C / B♯",
    "C♯ / D♭",
    "D",
    "D♯ / E♭",
    "E / F♭",
    "F / E♯",
    "F♯ / G♭",
    "G",
    "G♯ / A♭"
]

def convert_note_slash_to_db(slash_note):
    note, octave = slash_note.split('/')
    if len(note) == 1:
        alter = 0
    else:
        match note[1]:
            case 'b':
                alter = -1
            case '#':
                alter = 1
            case _:
                raise Exception('note should be 1 letter: ' + slash_note)
        note = note[0]
    return f'{note} {alter} {octave}'

def order_notes_around_central_location(notes):
    """Order notes by proximity to the midpoint of the given range.

    Input notes are strings in the format "<NOTE> <ALTER> <OCTAVE>", e.g., "C 0 4", "F 1 3", "B -1 5".
    The function computes a linear pitch value for each note (in semitones), finds the midpoint between the
    lowest and highest note in the provided list, and returns the notes ordered by their absolute distance
    to that midpoint (closest first).

    When two notes are at the same distance to the midpoint, their relative order is randomized to avoid bias.
    """
    if not notes or len(notes) <= 2:
        # Nothing to reorder (or ambiguous midpoint), return as-is
        return notes

    base_map = {
        "C": 0,
        "D": 2,
        "E": 4,
        "F": 5,
        "G": 7,
        "A": 9,
        "B": 11,
    }

    def note_value(note_str: str) -> int:
        note, alter_str, octave_str = note_str.split(" ")
        base = base_map[note]
        alter = int(alter_str)
        octave = int(octave_str)
        return octave * 12 + base + alter

    # Compute numeric values and the midpoint
    values = [note_value(n) for n in notes]
    lo, hi = min(values), max(values)
    midpoint = (lo + hi) / 2.0

    # Build list of (note, distance, is_above) and shuffle to randomize tie breaks
    indexed = list(notes)
    random.shuffle(indexed)

    def sort_key(n: str):
        v = note_value(n)
        # Primary: absolute distance to midpoint
        dist = abs(v - midpoint)
        # Secondary: prefer slightly above the midpoint over below when equal distances? The
        # spec says randomize on clashes; since we shuffled, ties will be randomized already.
        # Keep secondary stable to numeric to avoid TypeError; use 0 for all.
        return (dist, 0)

    # Sort by the key; because we shuffled first and Python's sort is stable,
    # equal-distance items will keep their randomized order
    ordered = sorted(indexed, key=sort_key)
    return ordered

def generate_notes(lowest_note, highest_note, include_crazy_notes=False):
    start_note, start_alter_str, start_octave_str = lowest_note.split(' ')
    end_note, end_alter_str, end_octave_str = highest_note.split(' ')

    start_alter = int(start_alter_str)

    start_octave = int(start_octave_str)
    end_octave = int(end_octave_str)

    current_octave = start_octave

    if len(start_note) > 1:
        raise Exception('note should be 1 letter: ' + lowest_note)

    if len(end_note) > 1:
        raise Exception('note should be 1 letter: ' + highest_note)

    compiled = []

    note_list = 'CDEFGAB'
    note_i = note_list.index(start_note)

    alter_list = [-1, 0, 1]

    alter_i = start_alter

    reached_end = False
    while not reached_end:

        current_note = note_list[note_i]
        is_last_octave = current_octave >= end_octave

        while alter_i <= 2:
            alter = alter_list[alter_i]
            alter_i += 1
            if is_last_octave and current_note == end_note:
                reached_end = True

            if not include_crazy_notes:
                if current_note == 'E' and alter == 1:
                    continue
                elif current_note == 'F' and alter == -1:
                    continue
                elif current_note == 'B' and alter == 1:
                    continue
                elif current_note == 'C' and alter == -1:
                    continue

            compiled.append(f"{current_note} {alter} {current_octave}")

        alter_i = 0

        note_i += 1
        if current_note == "B":
            note_i = 0
            current_octave += 1

    return compiled[1:-1]


def compile_notes_per_skilllevel(notes):
    per_skilllevel = {'Beginner': [], 'Intermediate': [], 'Advanced': []}
    for note in notes:
        rt = 1500 + random.randint(0, 1000)
        for sk in ['Beginner', 'Intermediate', 'Advanced']:
            per_skilllevel[sk].append({'note': note['note'],
                                       'octave': note['octave'],
                                       'alter': note['alter'], 'rt': rt})
            rt -= random.randint(0, 500) + 500
    return per_skilllevel


def serialise_notes(notes_str):
    """Serialise a semicolon-separated list of note strings.

    This function is intentionally strict and will raise if any note is malformed.
    Validation is covered by tests; no internal try/except here to avoid hiding issues.
    """
    serialised_notes = []
    for note in notes_str.split(';'):
        serialised_note = serialise_note(note)
        serialised_notes.append(serialised_note)
    return serialised_notes


def serialise_note(note_str):
    note, alter, octave = note_str.split(' ')
    return {
        'note': note,
        'octave': octave,
        'alter': alter,
        'reaction_time': '',
        'n': 0,
        'reaction_time_log': [],
        'correct': [],
    }

def toCamelCase(string):
    if not string:
        return string
        # Split the string by hyphens and filter out empty strings
    # Capitalize first letter of each word
    words = [word.capitalize() for word in string.split('-') ]
    # Join the words back together
    return ' '.join(words)


def generate_serialised_notes(instrument, level):
    # Resolve instrument to canonical name and normalize level
    canonical = resolve_instrument(instrument)
    if not canonical:
        raise ValueError(f"Unknown instrument: {instrument}")
    level = level.capitalize() if level else level

    instrument_notes_info = instruments[canonical][level]

    # this is for beginner levels where we have a specified list of ordered notes
    if 'notes' in instrument_notes_info and instrument_notes_info['notes'] is not None:
        instrument_notes = instrument_notes_info['notes']
        return serialise_notes(instrument_notes)

    notes_list = generate_notes(lowest_note=instrument_notes_info['lowest_note'],
                                highest_note=instrument_notes_info['highest_note'])

    notes_list = order_notes_around_central_location(notes_list)

    return [serialise_note(note) for note in notes_list]


def get_instrument_range(instrument: str, level: str):
    canonical = resolve_instrument(instrument)
    if not canonical:
        return None, None
    level = level.capitalize() if level else level

    instrument_notes_info = instruments[canonical][level]
    if 'notes' in instrument_notes_info and instrument_notes_info['notes'] is not None:
        _notes = instrument_notes_info['notes'].split(';')
        return _notes[0], _notes[-1]
    return instrument_notes_info['lowest_note'], instrument_notes_info['highest_note']


def sort_notes(grouped_by_note):
    import re

    # Define the proper ordering of notes within an octave
    NOTE_ORDER = ["C", "C#", "Db", "D", "D#", "Eb", "E", "F", "F#", "Gb", "G", "G#", "Ab", "A", "A#", "Bb", "B"]

    # Extended sorting logic for notes with octaves
    def note_sort_key(note):
        """
        Sorts musical notes based on their order in NOTE_ORDER and their octave.
        Args:
            note (str): A note with an accidental and octave, e.g., "F3b", "C4#", or "G#2".
        Returns:
            tuple: A tuple (octave, note_index) for sorting.
        """
        # Parse the note using regex: Capture the base note, alterations and the octave
        match = re.match(r"([A-G]+[#b]*)(\d+)", note)  # E.g., "F3b" -> ["F3b", "F3", "3"]
        if match:
            note_base, octave = match.groups()
            octave = int(octave)  # Convert octave to an integer
            # Handle flats and sharps
            if note_base not in NOTE_ORDER and "b" in note_base:
                # Convert flats to sharps for equivalence
                flat_to_sharp = {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#"}
                note_base = flat_to_sharp.get(note_base, note_base)
            note_index = NOTE_ORDER.index(note_base) if note_base in NOTE_ORDER else float('inf')
            return (octave, note_index)
        else:
            # Return high values for invalid notes to push them to the end
            return (float('inf'), float('inf'))

    # Sort grouped_by_note dictionary by its keys
    sorted_grouped_by_note = {key: grouped_by_note[key] for key in sorted(grouped_by_note.keys(), key=note_sort_key)}

    # Output the sorted dictionary
    return sorted_grouped_by_note


def compute_signatures(signatures):
    raw_sigs = signatures or ''
    selected_signatures = []
    if isinstance(raw_sigs, str) and raw_sigs.strip():
        try:
            selected_signatures = [int(x) for x in raw_sigs.split(',') if x.strip() != '']
        except ValueError:
            selected_signatures = []
    # Bound to [-7, 7] and unique while preserving order
    seen = set()
    filtered_sigs = []
    for s in selected_signatures:
        if -7 <= s <= 7 and s not in seen:
            seen.add(s)
            filtered_sigs.append(s)
    return filtered_sigs or [0]


def normalize_and_slug(value: str):
    """Normalize accidentals and return slug-safe variant.

    Args:
        value: A key-like string that may contain 'sharp' or 'flat' tokens or '#'/'b'.

    Returns:
        tuple[str, str]: (normalized_value, slug_value)
            - normalized_value uses '#'/'b'
            - slug_value replaces '#' with 'sharp' and 'b' with 'flat' for URL safety
    """
    if not value:
        return "", ""
    normalized = normalize_accidentals(value)
    slug = normalized.replace('#', 'sharp').replace('b', 'flat') if normalized else ""
    return normalized, slug

def normalize_accidentals(value: str) -> str:
    """Convert 'sharp'/'flat' tokens to '#'/'b' in a key-like string."""
    if not isinstance(value, str):
        return value
    if 'sharp' in value:
        return value.replace('sharp', '#')
    if 'flat' in value:
        return value.replace('flat', 'b')
    return value
