import copy
from datetime import timedelta
from typing import Any, List
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone
from django.utils.timezone import now
from model_utils.models import TimeStampedModel

from notes import tools
from notes.instrument_data import instruments

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


class BlankTransposingKey(models.TextChoices):
    BLANK = "BL", "None"

transposing_choices = BlankTransposingKey.choices + InstrumentKeys.choices


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
    label = models.CharField(max_length=64, null=True, blank=True, help_text='If you have lots of learning scenarios, it might help to give them memorable names')
    instrument_name = models.CharField(max_length=64, null=True, blank=True)
    level = models.CharField(max_length=64, choices=LevelChoices.choices, default=LevelChoices.BEGINNER)
    notes = models.JSONField(null=True, blank=True)
    clef = models.CharField(max_length=64, choices=ClefChoices.choices, default=ClefChoices.TREBLE)
    key = models.CharField(max_length=2, choices=InstrumentKeys.choices, default=NoteChoices.C)
    transpose_key = models.CharField(max_length=2, choices=transposing_choices,
                                     default=BlankTransposingKey.BLANK , help_text='This is an advanced option. Leave as None if unsure')

    ux = models.JSONField(default=dict, blank=True)

    def save(self, *args: Any, **kwargs: Any) -> None:
        # instrument can be null as we create a blank instence before user specifies this
        if self.instrument_name and not self.notes:

            if self.level == LevelChoices.BEGINNER:
                _notes = instruments[self.instrument_name][self.level]['notes']
                self.notes = _notes.split(';')
            else:
                lowest_note, highest_note = tools.get_instrument_range(self.instrument_name, self.level)
                notes = tools.generate_notes(highest_note=highest_note, lowest_note=lowest_note)
                self.notes = notes
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

        freshen_progress = False

        if package is None or package.older_than(hours=24):
            package = NoteRecordPackage.objects.create(learningscenario_id=learningscenario_id)
            freshen_progress = True

        if progress is None or freshen_progress:
            progress = []

        learningscenario: LearningScenario = LearningScenario.objects.get(id=learningscenario_id)

        progress = LearningScenario._add_new_notes(learningscenario.notes, progress)
        progress = LearningScenario._remove_deleted_notes(learningscenario.notes, progress)

        return package, progress

    @staticmethod
    def _add_new_notes(note_records:List[str], progress):
        flattened_progress = [f'{note['note']} {note['alter']} {note['octave']}' for note in progress]
        for noterecord in note_records:
            if noterecord not in flattened_progress:
                fresh_noterecord = tools.serialise_note(noterecord)
                progress.append(fresh_noterecord)
        return progress

    @staticmethod
    def _remove_deleted_notes(note_records:List[str], progress):
        for note_obj in progress:
            flattened_note = f'{note_obj["note"]} {note_obj["alter"]} {note_obj["octave"]}'
            if flattened_note not in note_records:
                progress.remove(note_obj)
        return progress

    def edit_notes(self, added, removed, commit=True):
        for note_str in added:
            self.notes.append(note_str)
        for note_str in removed:
            self.notes.remove(note_str)
        if commit:
            self.save()

    def clone(self):
        obj_copy = copy.deepcopy(self)
        obj_copy.pk = None
        obj_copy.label += ' copy'
        obj_copy.save()
        return obj_copy

    def get_transposeKey(self):
        if self.transpose_key == BlankTransposingKey.BLANK:
            return self.key
        return self.transpose_key

    @classmethod
    def add_history(cls, learningscenarios):
        # For each learning scenario, get practice history from the date of creation
        for scenario in learningscenarios:
            # Initialize practice history dictionary
            practice_history = {}

            # Get the creation date of the learning scenario
            creation_date = scenario.created.date()
            today = now().date()
            days_since_creation = (today - creation_date).days

            # Get all practice sessions for this learning scenario
            packages = NoteRecordPackage.objects.filter(
                learningscenario=scenario
            )

            # Create a dictionary with dates as keys and practice status as values
            for i in range(days_since_creation + 1):  # +1 to include today
                date = today - timedelta(days=i)
                date_str = date.strftime("%Y-%m-%d")
                practice_history[date_str] = False

            # Mark dates with practice sessions as True
            for package in packages:
                date_str = package.created.date().strftime("%Y-%m-%d")
                practice_history[date_str] = True

            # Calculate current streak
            streak_count = 0
            current_date = today

            # Count consecutive days with practice, starting from today and going backwards
            while True:
                date_str = current_date.strftime("%Y-%m-%d")
                if date_str in practice_history and practice_history[date_str]:
                    streak_count += 1
                    current_date = current_date - timedelta(days=1)
                else:
                    break

            # Sort practice history by date (oldest first)
            sorted_practice_history = {k: practice_history[k] for k in sorted(practice_history.keys())}

            # Add practice history and streak count to the learning scenario object
            scenario.practice_history = sorted_practice_history
            scenario.streak_count = streak_count


class NoteRecord(TimeStampedModel):
    """
    Model to store individual note practice results.
    Each record represents a single note practice attempt.
    """
    learningscenario = models.ForeignKey(LearningScenario, on_delete=models.CASCADE)
    note = models.CharField(max_length=1)  # e.g., 'A', 'B', 'C', etc.
    alter = models.CharField(max_length=2, blank=True)  # e.g., '1' for sharp, '-1' for flat
    octave = models.CharField(max_length=1)  # e.g., '3', '4', etc.
    reaction_time = models.IntegerField()  # in milliseconds
    correct = models.BooleanField()  # True if the answer was correct, False otherwise

    def __str__(self):
        note_str = f"{self.note}"
        if self.alter == '1':
            note_str += '#'
        elif self.alter == '-1':
            note_str += 'b'
        note_str += f"/{self.octave}"
        return f"{note_str} - {self.correct} - {self.reaction_time}ms"

    @property
    def user(self):
        return self.learningscenario.user

    @property
    def instrument(self):
        return self.learningscenario.instrument_name


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

    def add_result(self, json_data):
        """
        Add a result to the log. If the combination of alter, note, and octave already exists in the log,
        update that element. Otherwise, add the entire json_data to the log.

        Args:
            json_data (dict): Data containing alter, note, octave, correct, and reaction_time
        """
        # Initialize log if it's None
        if self.log is None:
            self.log = []

        # Extract the key fields from json_data
        alter = json_data.get('alter', '0')
        note = json_data.get('note', '')
        octave = json_data.get('octave', '')
        correct = json_data.get('correct', False)
        reaction_time = json_data.get('reaction_time', '')

        # Check if this note combination already exists in the log
        found = False
        for item in self.log:
            if (item.get('alter') == alter and
                item.get('note') == note and
                item.get('octave') == octave):
                # Found a match, update this item
                found = True

                # Initialize correct and reaction_time_log lists if they don't exist
                if 'correct' not in item or not isinstance(item['correct'], list):
                    item['correct'] = []
                if 'reaction_time_log' not in item or not isinstance(item['reaction_time_log'], list):
                    item['reaction_time_log'] = []

                # Add the new data to the lists
                item['correct'].append(correct)
                item['reaction_time_log'].append(int(reaction_time) if reaction_time else 0)

                # Update n (count of attempts)
                item['n'] = len(item['correct'])
                break

        # If no match was found, add the new item to the log
        if not found:
            new_item = {
                'alter': alter,
                'note': note,
                'octave': octave,
                'correct': [correct] if correct is not None else [],
                'reaction_time_log': [int(reaction_time) if reaction_time else 0],
                'n': 1
            }
            self.log.append(new_item)

        # Save the updated log
        self.save()

    def process_answers(self, json_data):
        self.log = json_data
        self.save()

        # Also create individual NoteRecord entries for each note in the json_data
        for note_data in json_data:
            # For each reaction time and correct value pair, create a NoteRecord
            for i in range(len(note_data.get('reaction_time_log', []))):
                if i < len(note_data.get('correct', [])):  # Ensure we have a corresponding correct value
                    NoteRecord.objects.create(
                        learningscenario=self.learningscenario,
                        note=note_data.get('note', ''),
                        alter=note_data.get('alter', ''),
                        octave=note_data.get('octave', ''),
                        reaction_time=note_data.get('reaction_time_log', [])[i],
                        correct=note_data.get('correct', [])[i]
                    )
