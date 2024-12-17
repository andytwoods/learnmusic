import factory
from notes.models import Note


class NoteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Note

    note = factory.Iterator(['A', 'B', 'C', 'D', 'E', 'F', 'G'])  # Randomly cycling through base notes
    alter = factory.Iterator([-1, 0, 1])  # Randomly choose from SHARP (1), NATURAL (0), FLAT (-1)
    octave = factory.Iterator(
        range(Note.LOWEST_OCTAVE, Note.HIGHEST_OCTAVE))  # Range from LOWEST_OCTAVE to HIGHEST_OCTAVE
