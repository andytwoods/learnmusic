import json
import random


def populate_vocab(octave: int, lowest_note: str, highest_note: str):
    from notes.models import Note
    return Note.objects.filter(octave__in=[3, 4])


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


def generate_notes(lowest_note, highest_note, include_crazy_notes=False):
    from notes.models import Note

    start_note = lowest_note.note
    end_note = highest_note.note

    start_octave = lowest_note.octave
    end_octave = highest_note.octave

    start_alter = lowest_note.alter
    end_alter = highest_note.alter

    current_octave = start_octave

    compiled = []

    note_list = 'CDEFGAB'
    note_i = note_list.index(start_note)

    alter_list = [-1, 0, 1]
    end_alter_i = alter_list.index(end_alter)
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

            note, created = Note.objects.get_or_create(note=current_note, octave=current_octave, alter=alter)
            if created:
                note.save()
            compiled.append(note)

        alter_i = 0

        note_i += 1
        if current_note == "B":
            note_i = 0
            current_octave += 1

    return compiled[1:-1]


def generate_notes_from_str(notes_str):
    from notes.models import Note

    compiled = []

    for note_info in notes_str.split(';'):
        note_str, altar_str, octave_str = note_info.split(' ')
        note, created = Note.objects.get_or_create(note=note_str, octave=int(octave_str), alter=int(altar_str))
        if created:
            note.save()
        compiled.append(note)

    return compiled


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


def generate_progress_from_str_notes(notes_str):
    notes = notes_str.split(';')
    progress = []
    for note_str in notes:
        note, alter, octave = note_str.split(' ')
        note_info = {'note': note,
                     'alter': int(alter),
                     'octave': int(octave),
                     'n': 0,
                     'reaction_time': None,
                     }
        progress.append(note_info)
    return progress
