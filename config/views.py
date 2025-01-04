from django.shortcuts import render
from django.urls import reverse

from notes.models import Instrument


def home(request):
    instruments_info = {}
    instrument: Instrument
    for instrument in Instrument.objects.all().order_by('name'):
        if instrument.name not in instruments_info:
            instruments_info[instrument.name] = []

        instrument_info = {'level': instrument.level,
                           'id': instrument.id,
                           'notes': instrument.notes_str,
                           'clef': instrument.clef
                           }
        instruments_info[instrument.name].append(instrument_info)

    # I broke the homepage when randomly updating the url to practice-try...
    # I don't want to repeat this mistake
    practice_url = reverse('practice-try', kwargs={
        'instrument': 'dummy',
        'clef': 'dummy',
        'level': 'dummy'}).split('/')[1]

    context = {'instruments': instruments_info,
               'practice_url': practice_url}
    return render(request, template_name="pages/home.html", context=context)
