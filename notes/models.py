import json
from collections import namedtuple
from django.utils import timezone
from typing import Any

from click.core import batch
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from model_utils.models import TimeStampedModel

from django.contrib.auth import get_user_model

from notes import tools

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
        if "/" in note_str:
            note_str, octave_str = note_str.split('/')
            alter_str = "0"
            if 'b' in note_str:
                alter_str = "-1"
            elif '#' in note_str:
                alter_str = "1"
            note_str = note_str[0]
        else:
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
        ("Trumpet", "Beginner", None, None, ClefChoices.TREBLE, 'C 0 4;D 0 4;E 0 4;F 0 4;G 0 4;A 0 4;Bb -1 4;B 0 4'),
        ("Trumpet", "Intermediate", "F 1 3", "C 0 5", ClefChoices.TREBLE),
        ("Trumpet", "Advanced", "F 1 3", "C 0 6", ClefChoices.TREBLE),
    )

    @staticmethod
    def get_instrument_range(instrument_name: str, level:str='Advanced'):
        instrument = Instrument.objects.get(name=instrument_name, level=level)
        return [instrument.lowest_note, instrument.highest_note]

    def __str__(self):
        return f"{self.name} {self.level}"

    @classmethod
    def get_instrument(cls, instrument_name):
        return cls.objects.get(name=instrument_name)

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
            if len(instrument_info) >= 5:
                instrument.notes_str = instrument_info[5]

            instruments.append(instrument)

        Instrument.objects.bulk_create(instruments)

    name = models.CharField(max_length=64)
    level = models.CharField(max_length=64,
                             choices=LevelChoices.choices,
                             default=LevelChoices.BEGINNER)
    clef = models.CharField(max_length=64, choices=ClefChoices.choices, default=ClefChoices.TREBLE)
    lowest_note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name='instrument_lowest_note', null=True,
                                    blank=True)
    highest_note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name='instrument_highest_note', null=True,
                                     blank=True)
    notes_str = models.CharField(max_length=512, default='')


class LearningScenario(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE, null=True, blank=True)
    vocabulary = models.ManyToManyField(Note)
    clef = models.CharField(max_length=64, choices=ClefChoices.choices, default=ClefChoices.TREBLE)

    def save(self, *args: Any, **kwargs: Any) -> None:
        # instrument can be null as we create a blank instence before user specifies this
        if self.instrument and not self.vocabulary.exists():
            highest_note = self.instrument.highest_note
            lowest_note = self.instrument.lowest_note
            if highest_note and lowest_note:
                notes = tools.generate_notes(highest_note=highest_note,
                                             lowest_note=lowest_note)
            else:
                notes = tools.generate_notes_from_str(self.instrument.notes_str)

            self.vocabulary.add(*notes)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.id}'

    def last_practiced(self):
        try:
            date_last_practiced = NoteRecordPackage.objects.filter(learningscenario=self).last().created
            difference = timezone.now() - date_last_practiced
        except AttributeError:
            return "Never"
        if difference.days == 0:
            return "Today"
        return difference.days

    def days_old(self):
        difference = timezone.now() - self.created
        return difference.days

    @staticmethod
    def check_younger_than_24hrs(created):
        difference = timezone.now() - created
        return difference.days < 1

    @staticmethod
    def progress_latest_serialised(learningscenario_id: int):

        package = NoteRecordPackage.objects.filter(learningscenario_id=learningscenario_id).last()
        if package and LearningScenario.check_younger_than_24hrs(package.created):
            noterecords = package.noterecords.all()
        else:
            package, noterecords = NoteRecordPackage.generate_package(learningscenario_id)

        progress = []

        def note_key(nr):
            return f"{nr['note']} {nr['alter']} {nr['octave']}"

        old_noterecords = {}
        if package.log:
            for old_noterecord in package.log:
                old_noterecords[note_key(old_noterecord)] = old_noterecord

        for noterecord in noterecords:
            fresh_noterecord = noterecord.serialise()
            existing_nr_data = old_noterecords.get(note_key(fresh_noterecord), None)
            if existing_nr_data:
                progress.append(existing_nr_data)
            else:
                progress.append(fresh_noterecord)

        return package, progress

    def simple_vocab(self):
        vocab = [str(note) for note in self.vocabulary.all()]
        return vocab

    def edit_notes(self, added, removed):
        for note_str in added:
            note = Note.get_from_str(note_str)
            self.vocabulary.add(note)
        for note_str in removed:
            note = Note.get_from_str(note_str)
            self.vocabulary.remove(note)


class NoteRecord(TimeStampedModel):
    note = models.ForeignKey(Note, on_delete=models.CASCADE)
    learningscenario = models.ForeignKey(LearningScenario, on_delete=models.CASCADE)
    reaction_time = models.PositiveIntegerField(null=True, blank=True)
    n = models.PositiveIntegerField(default=0)

    def serialise(self):
        return {
            'note': self.note.note,
            'octave': self.note.octave,
            'alter': self.note.alter,
            'reaction_time': self.reaction_time,
            'n': self.n,
        }

    def __str__(self):
        return f"{self.note} --- {self.created.strftime('%Y-%m-%d')}"


class NoteRecordPackage(TimeStampedModel):
    learningscenario = models.ForeignKey(LearningScenario, on_delete=models.CASCADE)
    noterecords = models.ManyToManyField(NoteRecord)
    log_minimal = models.TextField(null=True, blank=True)
    log = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.learningscenario} {self.created}"

    def user(self):
        return self.learningscenario.user

    def instrument(self):
        return self.learningscenario.instrument

    @classmethod
    def generate_package(cls, learningscenario_id: int):
        records = []
        learningscenario = LearningScenario.objects.get(id=learningscenario_id)
        for note in Note.objects.filter(learningscenario=learningscenario):
            record: NoteRecord = NoteRecord(note=note, learningscenario=learningscenario)
            records.append(record)
        NoteRecord.objects.bulk_create(records)

        package: NoteRecordPackage = NoteRecordPackage(learningscenario=learningscenario)
        package.save()
        package.noterecords.set(records)

        return package, records

    def process_answers(self, json_data):
        self.log = json_data
        self.save()


