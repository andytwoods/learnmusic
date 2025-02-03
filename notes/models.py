from typing import Any
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone
from model_utils.models import TimeStampedModel

from notes import tools
from notes.instruments import instruments

User = get_user_model()

class InstrumentKeys(models.TextChoices):
    A = "A", "A"
    A_SHARP = "A#", "A#"
    A_FLAT = "Ab", "Ab"
    B = "B", "B"
    B_FLAT = "Bb", "Bb"
    C = "C", "C"
    C_SHARP = "C#", "C#"
    D = "D", "D"
    D_SHARP = "D#", "D#"
    D_FLAT = "Db", "Db"
    E = "E", "E"
    E_FLAT = "Eb", "Eb"
    F = "F", "F"
    F_SHARP = "F#", "F#"
    G = "G", "G"
    G_SHARP = "G#", "G#"
    G_FLAT = "Gb", "Gb"


class NoteChoices(models.TextChoices):
    A = 'A'
    B = 'B'
    C = 'C'
    D = 'D'
    E = 'E'
    F = 'F'
    G = 'G'


class ClefChoices(models.TextChoices):
    TREBLE = 'Treble'
    TENOR = 'Tenor'
    ALTO = 'Alto'
    BASS = 'Bass'


class LevelChoices(models.TextChoices):
    BEGINNER = 'Beginner'
    INTERMEDIATE = 'Intermediate'
    ADVANCED = 'Advanced'



class LearningScenario(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    instrument_name = models.CharField(max_length=64, null=True, blank=True)
    level = models.CharField(max_length=64,choices=LevelChoices.choices, default=LevelChoices.BEGINNER)
    notes = models.JSONField(null=True, blank=True)
    clef = models.CharField(max_length=64, choices=ClefChoices.choices, default=ClefChoices.TREBLE)
    key = models.CharField(max_length=2, choices=InstrumentKeys.choices, default=NoteChoices.C)
    transposing_direction = models.IntegerField(default=0, validators=[
        MinValueValidator(-1),
        MaxValueValidator(1),
    ])

    def save(self, *args: Any, **kwargs: Any) -> None:
        # instrument can be null as we create a blank instence before user specifies this
        if self.instrument_name and not self.notes:

            if self.level == LevelChoices.BEGINNER:
                _notes = instruments[self.instrument_name][self.level]['notes']
                self.notes = _notes.split(';')
            else:
                lowest_note, highest_note = tools.get_instrument_range(self.instrument_name, self.level)
                notes = tools.generate_notes(highest_note=highest_note, lowest_note=lowest_note)
                self.notes = ';'.join(notes)
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
    def progress_latest_serialised(learningscenario_id: int):

        package: NoteRecordPackage = NoteRecordPackage.objects.filter(learningscenario_id=learningscenario_id).last()
        progress = package.log if package else None

        freshen_progess = False

        if package is None or package.older_than(hours=24):
            package = NoteRecordPackage.objects.create(learningscenario_id=learningscenario_id)
            freshen_progess = True

        if progress is None or freshen_progess:
            progress = []
            learningscenario: LearningScenario = LearningScenario.objects.get(id=learningscenario_id)
            for noterecord in learningscenario.notes:
                fresh_noterecord = tools.serialise_note(noterecord)
                progress.append(fresh_noterecord)

        return package, progress

    def edit_notes(self, added, removed):
        for note_str in added:
            self.notes.append(note_str)
        for note_str in removed:
            self.notes.remove(note_str)


class NoteRecordPackage(TimeStampedModel):
    learningscenario = models.ForeignKey(LearningScenario, on_delete=models.CASCADE)
    log = models.JSONField(null=True, blank=True)

    def older_than(self, hours: int):
        difference = timezone.now() - self.created
        difference_in_hours = difference.total_seconds() / 3600
        return difference_in_hours > hours


    def __str__(self):
        return f"{self.learningscenario} {self.created}"

    def user(self):
        return self.learningscenario.user

    def instrument(self):
        return self.learningscenario.instrument

    def process_answers(self, json_data):
        self.log = json_data
        self.save()
