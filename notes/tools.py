import random
from unittest import case

from notes.instruments import instruments

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
    per_skilllevel = {'beginner': [], 'intermediate': [], 'advanced': []}
    for note in notes:
        rt = 1500 + random.randint(0, 1000)
        for sk in ['beginner', 'intermediate', 'advanced']:
            per_skilllevel[sk].append({'note': note['note'],
                                       'octave': note['octave'],
                                       'alter': note['alter'], 'rt': rt})
            rt -= random.randint(0, 500) + 500
    return per_skilllevel


def serialise_notes(notes_str):
    serialised_notes = []
    for note in notes_str.split(';'):
        serialised_notes.append(serialise_note(note))
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


def generate_serialised_notes(instrument, level):
    instrument_notes_info = instruments[instrument][level]
    if 'notes' in instrument_notes_info and instrument_notes_info['notes'] is not None:
        return serialise_notes(instrument_notes_info['notes'])

    notes_list = generate_notes(lowest_note=instrument_notes_info['lowest_note'],
                                highest_note=instrument_notes_info['highest_note'])

    return [serialise_note(note) for note in notes_list]


def get_instrument_range(instrument:str, level:str):
    instrument_notes_info = instruments[instrument][level]
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
