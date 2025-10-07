import json
import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model

from notes.factories import UserFactory
from notes.models import LearningScenario, LevelChoices, ClefChoices

pytestmark = pytest.mark.django_db


def create_learningscenario(user, signatures=None):
    ls = LearningScenario.objects.create(
        user=user,
        instrument_name="Trumpet",
        level=LevelChoices.BEGINNER,
        clef=ClefChoices.TREBLE,
        relative_key="C",
        octave_shift=0,
    )
    if signatures is not None:
        ls.signatures = signatures
        ls.save()
    return ls


def test_progress_latest_serialised_returns_wrapped_notes_and_signatures(client):
    user = UserFactory()
    ls = create_learningscenario(user, signatures=[0, 1, -2])

    package, progress = LearningScenario.progress_latest_serialised(ls.id)
    assert isinstance(progress, dict)
    assert "notes" in progress and isinstance(progress["notes"], list)
    assert "signatures" in progress and isinstance(progress["signatures"], dict)
    assert progress["signatures"]["fifths"] == [ -2, 0, 1 ] or progress["signatures"]["fifths"] == [0,1,-2]
    # vexflow names should correspond to the sorted fifths sequence
    vf = progress["signatures"]["vexflow"]
    assert all(isinstance(x, str) for x in vf)
    assert len(vf) == len(progress["signatures"]["fifths"])  # same length


def test_practice_view_embeds_wrapped_progress(client):
    user = UserFactory()
    ls = create_learningscenario(user, signatures=[0])

    client.login(username="u2", password="p")
    resp = client.get(reverse("practice", kwargs={"learningscenario_id": ls.id}))
    assert resp.status_code == 200
    # progress is provided to template context
    progress = resp.context["progress"]
    assert isinstance(progress, dict)
    assert "notes" in progress and "signatures" in progress
