import random

import factory
from faker import Faker

from notes.models import Note, User, Instrument, LevelChoices, ClefChoices, LearningScenario

fake = Faker()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.LazyAttribute(lambda _: fake.email())
    password = factory.PostGenerationMethodCall('set_password', 'password123')  # Default test password


class NoteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Note

    note = factory.Iterator(['A', 'B', 'C', 'D', 'E', 'F', 'G'])  # Randomly cycling through base notes
    alter = factory.Iterator([-1, 0, 1])  # Randomly choose from SHARP (1), NATURAL (0), FLAT (-1)
    octave = factory.Iterator(
        range(Note.LOWEST_OCTAVE, Note.HIGHEST_OCTAVE))  # Range from LOWEST_OCTAVE to HIGHEST_OCTAVE


class InstrumentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Instrument

    name = factory.LazyAttribute(lambda _: fake.user_name())
    level = factory.LazyFunction(lambda: random.choice(LevelChoices.choices))
    clef = factory.LazyFunction(lambda: random.choice(ClefChoices.choices))

    lowest_note = factory.SubFactory(NoteFactory)
    highest_note = factory.SubFactory(NoteFactory)


class LearningScenarioFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LearningScenario

    user = factory.SubFactory(UserFactory)
    instrument = factory.SubFactory(InstrumentFactory)
    clef = factory.LazyFunction(lambda: random.choice(ClefChoices.choices))
