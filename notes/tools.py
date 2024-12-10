from notes.models import Note


def populate_vocab(octave: int, lowest_note: str, highest_note: str):
    return Note.objects.filter(octave__in=[3,4])
