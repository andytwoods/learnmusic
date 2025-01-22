import random

import factory
from faker import Faker

from notes.models import User, LevelChoices, ClefChoices, LearningScenario

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
