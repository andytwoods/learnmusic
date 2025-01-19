import random

import factory
from faker import Faker

from notes.models import User, Instrument, LevelChoices, ClefChoices, LearningScenario

fake = Faker()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.LazyAttribute(lambda _: fake.email())
    password = factory.PostGenerationMethodCall('set_password', 'password123')  # Default test password



class InstrumentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Instrument

    name = factory.LazyAttribute(lambda _: fake.user_name())
    level = factory.LazyFunction(lambda: random.choice(LevelChoices.choices))
    clef = factory.LazyFunction(lambda: random.choice(ClefChoices.choices))



class LearningScenarioFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LearningScenario

    user = factory.SubFactory(UserFactory)
    instrument = factory.SubFactory(InstrumentFactory)
    clef = factory.LazyFunction(lambda: random.choice(ClefChoices.choices))
