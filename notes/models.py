import copy
from datetime import timedelta
from typing import Any, List

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.timezone import now
from model_utils.models import TimeStampedModel

from notes import tools
from notes.instrument_data import instruments

User = get_user_model()

from django.db import models
from django.core.exceptions import ValidationError


class ProgressWrapper(dict):
    """A dict that behaves like a list of notes for backward compatibility.

    - progress['notes'] -> list of note dicts
    - progress['signatures'] -> signatures payload
    - progress[i] -> ith note (list-like)
    - len(progress) -> len(notes)
    - iter(progress) -> iterate over notes
    """
    def __init__(self, notes, signatures_payload):
        super().__init__()
        super().__setitem__('notes', notes)
        super().__setitem__('signatures', signatures_payload)

    def __getitem__(self, key):
        if isinstance(key, int):
            return super().__getitem__('notes')[key]
        return super().__getitem__(key)

    def __len__(self):
        return len(super().__getitem__('notes'))

    def __iter__(self):
        return iter(super().__getitem__('notes'))


def validate_signatures_array(value):
    # Must be a list of unique integers in [-7, 7]
    if not isinstance(value, list):
        raise ValidationError("Signatures must be a list.")
    if any(not isinstance(v, int) for v in value):
        raise ValidationError("All signatures must be integers.")
    if any(v < -7 or v > 7 for v in value):
        raise ValidationError("Signatures must be between -7 and 7.")
    if len(value) != len(set(value)):
        raise ValidationError("Signatures must not contain duplicates.")


# optional: canonical mapping for rendering in VexFlow (major spelling is fine)
FIFTHS_TO_VEXFLOW_MAJOR = {
    0: "C", 1: "G", 2: "D", 3: "A", 4: "E", 5: "B", 6: "F#", 7: "C#",
    -1: "F", -2: "Bb", -3: "Eb", -4: "Ab", -5: "Db", -6: "Gb", -7: "Cb",
}


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


class BlankAbsolutePitch(models.TextChoices):
    BLANK = "BL", "None"


absolute_pitch_choices = BlankAbsolutePitch.choices + InstrumentKeys.choices


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
    class Reminder(models.TextChoices):
        ALL = 'AL', 'All notifications'
        EMAIL = 'EM', 'Email'
        PUSH_NOTIFICATION = 'PN', 'Push notification'
        NONE = 'NO', 'No reminder'

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    label = models.CharField(max_length=64, null=True, blank=True,
                             help_text='If you have lots of learning scenarios, it might help to give them memorable '
                                       'names')
    instrument_name = models.CharField(max_length=64, null=True, blank=True)
    level = models.CharField(max_length=64, choices=LevelChoices.choices, default=LevelChoices.BEGINNER)
    notes = models.JSONField(null=True, blank=True)
    clef = models.CharField(max_length=64, choices=ClefChoices.choices, default=ClefChoices.TREBLE)
    relative_key = models.CharField(max_length=2, choices=InstrumentKeys.choices, default=NoteChoices.C)
    octave_shift = models.SmallIntegerField(default=0,
                                            help_text="This is an advanced option. Leave as 0 if unsure. To shift the "
                                                      "octave down one, specify -1. To shift up one, specify 1.")
    absolute_pitch = models.CharField(max_length=2, choices=absolute_pitch_choices,
                                      default=BlankAbsolutePitch.BLANK,
                                      help_text='This is an advanced option. Leave as None if unsure.')

    reminder = models.DateTimeField(null=True, blank=True)
    reminder_type = models.CharField(max_length=2, choices=Reminder.choices, default=Reminder.NONE, null=True,
                                     blank=True, verbose_name="Daily reminder")


    # JSON array of ints (e.g. [0, 1, -2]) meaning: natural, 1♯, 2♭
    signatures = models.JSONField(
        default=list,
        blank=True,
        validators=[validate_signatures_array],
        help_text="JSON array of integers in [-7..7] – number of sharps (+) or flats (−).",
    )

    ux = models.JSONField(default=dict, blank=True)

    @property
    def signatures_sorted(self):
        try:
            return sorted(self.signatures)
        except Exception:
            return []

    @property
    def vexflow_keys(self):
        return [FIFTHS_TO_VEXFLOW_MAJOR[i] for i in self.signatures_sorted]

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

    # Backward-compatible alias for renamed field
    @property
    def absolute_key(self):
        return self.absolute_pitch

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
        progress_notes = package.log if package else None
        # If stored progress is a wrapped dict, extract notes list
        if isinstance(progress_notes, dict):
            progress_notes = progress_notes.get('notes', [])

        freshen_progress = False

        if package is None or package.older_than(hours=24):
            package = NoteRecordPackage.objects.create(learningscenario_id=learningscenario_id)
            freshen_progress = True

        if progress_notes is None or freshen_progress:
            progress_notes = []

        learningscenario: LearningScenario = LearningScenario.objects.get(id=learningscenario_id)

        progress_notes = LearningScenario._add_new_notes(learningscenario.notes, progress_notes)
        progress_notes = LearningScenario._remove_deleted_notes(learningscenario.notes, progress_notes)

        # Wrap with signatures info for downstream consumers expecting structured payload
        sigs = learningscenario.signatures_sorted or [0]
        signatures_payload = {
            'fifths': sigs,
            'vexflow': [FIFTHS_TO_VEXFLOW_MAJOR[s] for s in sigs],
        }
        progress_wrapped = ProgressWrapper(progress_notes, signatures_payload)

        return package, progress_wrapped

    @staticmethod
    def _add_new_notes(note_records: List[str], progress):
        flattened_progress = [f'{note['note']} {note['alter']} {note['octave']}' for note in progress]
        for noterecord in note_records:
            if noterecord not in flattened_progress:
                fresh_noterecord = tools.serialise_note(noterecord)
                progress.append(fresh_noterecord)
        return progress

    @staticmethod
    def _remove_deleted_notes(note_records: List[str], progress):
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

    def get_absolute_pitch(self):
        """Return the effective absolute pitch key.

        If absolute_pitch is blank (BL), fall back to relative_key.
        """
        if self.absolute_pitch == BlankAbsolutePitch.BLANK:
            return self.relative_key
        return self.absolute_pitch

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

    @classmethod
    def ingest_frontend_cache(cls, user, info, notes_history):
        """
        Create or find a LearningScenario for the given user based on the provided info dict,
        and persist the provided notes_history into a new NoteRecordPackage.

        Args:
            user: Django user
            info: dict with keys like instrument, level, clef, relative_key, shifted_octave, absolute_key
            notes_history: list of note progress dicts from the frontend

        Returns:
            (LearningScenario, NoteRecordPackage)
        """

        ls_defaults = {
            'label': None,
            'notes': None,
            'ux': {},
        }
        # Accept only new keys (legacy 'key' supported for relative only)
        rel_key = info.get('relative_key', info.get('key'))
        # Accept both new 'absolute_pitch' and legacy 'absolute_key'; default to blank sentinel if missing
        abs_pitch = info.get('absolute_pitch', info.get('absolute_key', BlankAbsolutePitch.BLANK))

        ls, created = cls.objects.get_or_create(
            user=user,
            instrument_name=info.get('instrument', ''),
            level=info.get('level'),
            clef=info.get('clef'),
            relative_key=rel_key,
            octave_shift=int(info.get('shifted_octave')),
            absolute_pitch=abs_pitch,
            defaults=ls_defaults,
        )

        package = NoteRecordPackage.objects.create(learningscenario=ls)
        package.process_answers(notes_history)

        return ls, package


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

        # Only create NoteRecord entries when json_data is a list of dicts
        if not isinstance(json_data, list):
            return

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
