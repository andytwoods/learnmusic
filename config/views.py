from django.shortcuts import render

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
    context = {'instruments': instruments_info}
    return render(request, template_name="pages/home.html", context=context)
