from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.conf import settings

from notes.instrument_data import instruments, instrument_infos


def home(request):
    # I broke the homepage when randomly updating the url to practice-try...
    # I don't want to repeat this mistake
    practice_url = reverse('practice-try', kwargs={
        'instrument': 'dummy',
        'key': 'dummy',
        'clef': 'dummy',
        'level': 'dummy',
        'octave': 0}).split('/')[1]

    instruments_data = {}
    for instrument, instrument_info in instruments.items():
        if instrument not in instruments_data:
            instruments_data[instrument] = {
                'clefs': instrument_infos[instrument]['clef'],
                'keys': instrument_infos[instrument]['common_keys']
            }
        instruments_data[instrument]['levels'] = [str(x) for x in instrument_info.keys()]

    context = {'instruments': instruments_data,
               'practice_url': practice_url,
               }
    return render(request, template_name="pages/home.html", context=context)


@staff_member_required
def test_rollbar(request):
    a = None
    a.hello()  # Creating an error with an invalid line of code
    return HttpResponse("Hello, world. You're at the pollapp index.")
