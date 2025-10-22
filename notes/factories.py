import random

import factory
from faker import Faker
from django.utils import timezone

from notes.models import User, LevelChoices, ClefChoices, LearningScenario, NoteChoices

fake = Faker()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    email = factory.LazyAttribute(lambda _: fake.email())

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        # Set a default password or use the provided one
        pwd = extracted or "password123"
        self.set_password(pwd)
        if create:
            self.save()




class LearningScenarioFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LearningScenario

    user = factory.SubFactory(UserFactory)
    clef = factory.LazyFunction(lambda: random.choice(ClefChoices.choices))
    instrument_name = 'Trumpet'
    level = 'Beginner'
    relative_key = 'Bb'
    notes = ["B -1 2", "C 0 3", "D 0 3"]


