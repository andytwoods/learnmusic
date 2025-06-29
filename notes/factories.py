import random

import factory
from faker import Faker
from django.utils import timezone

from notes.models import User, LevelChoices, ClefChoices, LearningScenario, NoteRecord, NoteChoices

fake = Faker()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.LazyAttribute(lambda _: fake.email())
    password = factory.PostGenerationMethodCall('set_password', 'password123')  # Default test password




class LearningScenarioFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LearningScenario

    user = factory.SubFactory(UserFactory)
    clef = factory.LazyFunction(lambda: random.choice(ClefChoices.choices))
    instrument_name = 'Trumpet'
    level = 'Beginner'
    key = 'Bb'
    notes = ["B -1 2", "C 0 3", "D 0 3"]


class NoteRecordFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = NoteRecord

    learningscenario = factory.SubFactory(LearningScenarioFactory)
    note = factory.LazyFunction(lambda: random.choice([choice[0] for choice in NoteChoices.choices]))
    alter = factory.LazyFunction(lambda: random.choice(['0', '1', '-1']))  # 0 = natural, 1 = sharp, -1 = flat
    octave = factory.LazyFunction(lambda: str(random.randint(3, 5)))  # Typical octave range
    reaction_time = factory.LazyFunction(lambda: random.randint(500, 3000))  # Reaction time in milliseconds
    correct = factory.LazyFunction(lambda: random.choice([True, False]))

    # TimeStampedModel fields
    created = factory.LazyFunction(lambda: timezone.now())
    modified = factory.LazyFunction(lambda: timezone.now())
