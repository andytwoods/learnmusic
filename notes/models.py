from collections import namedtuple

from click.core import batch
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from model_utils.models import TimeStampedModel

from django.contrib.auth import get_user_model

User = get_user_model()

from learnmusic import users


class Note(models.Model):

    def create_default_notes(*args, **kwargs):
        notes = []
        for octave in range(Note.LOWEST_OCTAVE, Note.HIGHEST_OCTAVE):
            for note_info in Note.BASE_NOTES:
                note = Note(note=note_info[0],
                            alter=note_info[1],
                            octave=octave)
                notes.append(note)

        Note.objects.bulk_create(notes)

    BASE_NOTES = [
        ('A', -1), ('A', 0), ('A', 1),
        ('B', -1), ('B', 0),
        ('C', 0), ('C', 1),
        ('D', -1), ('D', 0), ('D', 1),
        ('E', -1), ('E', 0),
        ('F', 0), ('F', 1),
        ('G', -1), ('G', 0), ('G', 1),
    ]

    class NoteChoices(models.TextChoices):
        A = 'A'
        B = 'B'
        C = 'C'
        D = 'D'
        E = 'E'
        F = 'F'
        G = 'G'

    class AlterChoices(models.IntegerChoices):
        # DOUBLE_SHARP = 2
        SHARP = 1
        NATURAL = 0
        FLAT = -1
        # DOUBLE_FLAT = -2

    LOWEST_OCTAVE = 0
    HIGHEST_OCTAVE = 9

    note = models.CharField(max_length=1, choices=NoteChoices.choices)
    alter = models.IntegerField(choices=AlterChoices.choices, default=0)
    octave = models.IntegerField(default=4,
                                 validators=[MinValueValidator(LOWEST_OCTAVE),
                                             MaxValueValidator(HIGHEST_OCTAVE)])

    def __str__(self):
        return f'{self.note} {self.alter} {self.octave}'

    @classmethod
    def get_from_str(cls, note_str: str):
        note_str, alter_str, octave_str = note_str.split(' ')
        note = Note.objects.get(note=note_str, octave=int(octave_str), alter=int(alter_str))
        return note


class ClefChoices(models.TextChoices):
    TREBLE = 'Treble'
    TENOR = 'Tenor'
    ALTO = 'Alto'
    BASS = 'Bass'


class LevelChoices(models.TextChoices):
    BEGINNER = 'Beginner'
    INTERMEDIATE = 'Intermediate'
    ADVANCED = 'Advanced'


class Instrument(models.Model):
    BASE_INSTRUMENTS = (
        ("Trumpet", "Beginner", "C 0 3", "G 0 3", ClefChoices.TREBLE),
        ("Trumpet", "Intermediate", "F 1 3", "C 0 5", ClefChoices.TREBLE),
        ("Trumpet", "Advanced", "F 1 3", "C 0 6", ClefChoices.TREBLE),
    )

    def __str__(self):
        return f"{self.name} {self.level}"

    def create_default_instruments(*args, **kwargs):
        instruments = []
        for instrument_info in Instrument.BASE_INSTRUMENTS:
            instrument: Instrument = Instrument(
                name=instrument_info[0],
                level=instrument_info[1],
                lowest_note=Note.get_from_str(instrument_info[2]),
                highest_note=Note.get_from_str(instrument_info[3]),
                clef=instrument_info[4],
            )
            instruments.append(instrument)

        Instrument.objects.bulk_create(instruments)

    name = models.CharField(max_length=64)
    level = models.CharField(max_length=64,
                             choices=LevelChoices.choices,
                             default=LevelChoices.BEGINNER)
    clef = models.CharField(max_length=64, choices=ClefChoices.choices, default=ClefChoices.TREBLE)
    lowest_note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name='instrument_lowest_note')
    highest_note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name='instrument_highest_note')


class LearningScenario(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    instrument = models.CharField(max_length=64, null=True, blank=True)
    vocabulary = models.ManyToManyField(Note)
    clef = models.CharField(max_length=64, choices=ClefChoices.choices, default=ClefChoices.TREBLE)

    def __str__(self):
        return f'{self.user} {self.instrument}'

class NoteRecord(TimeStampedModel):
    note = models.ForeignKey(Note, on_delete=models.CASCADE)
    learning_scheme = models.ForeignKey(LearningScenario, on_delete=models.CASCADE)
    reaction_time = models.PositiveIntegerField(null=True, blank=True)
    n = models.PositiveIntegerField(default=0)
