from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse

from notes.instruments import instruments
from notes.models import LevelChoices


def home(request):

    # I broke the homepage when randomly updating the url to practice-try...
    # I don't want to repeat this mistake
    practice_url = reverse('practice-try', kwargs={
        'instrument': 'dummy',
        'clef': 'dummy',
        'level': 'dummy'}).split('/')[1]

    context = {'instruments': [x for x in instruments.keys()],
               'levels': [x[1] for x in LevelChoices.choices],
               'practice_url': practice_url}
    return render(request, template_name="pages/home.html", context=context)


@staff_member_required
def test_rollbar(request):
    a = None
    a.hello()  # Creating an error with an invalid line of code
    return HttpResponse("Hello, world. You're at the pollapp index.")
