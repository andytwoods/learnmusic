from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from model_utils.models import TimeStampedModel

from django.contrib.auth import get_user_model

User = get_user_model()

from learnmusic import users


class Note(models.Model):
    class NoteChoices(models.TextChoices):
        A = 'A'
        B = 'B'
        C = 'C'
        D = 'D'
        E = 'E'
        F = 'F'
        G = 'G'

    class AlterChoices(models.IntegerChoices):
        DOUBLE_SHARP = 2
        SHARP = 1
        NATURAL = 0
        FLAT = -1
        DOUBLE_FLAT = -2

    note = models.CharField(max_length=1, choices=NoteChoices.choices)
    alter = models.IntegerField(choices=AlterChoices.choices, default=0)
    octave = models.IntegerField(default=4, validators=[MinValueValidator(0), MaxValueValidator(9)])

    def __str__(self):
        return f'{self.note}{self.alter:+d}{self.octave}'

class LearningInfo(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    notes = models.ManyToManyField(Note, through='NoteRecord')
    vocabulary = models.ManyToManyField(
        Note,
        through='NoteVocabulary',
        related_name='vocabulary'
    )

class NoteRecord(TimeStampedModel):
    note = models.ForeignKey(Note, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class NoteVocabulary(TimeStampedModel):
    notes = models.ManyToManyField(Note)
