from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage

from notes.instrument_data import instruments, instrument_infos


def home(request):
    # I broke the homepage when randomly updating the url to practice-try...
    # I don't want to repeat this mistake
    practice_url = reverse('practice-try-sigs', kwargs={
        'instrument': 'dummy',
        'key': 'dummy',
        'clef': 'dummy',
        'level': 'dummy',
        'octave': 0,
        'signatures': '0'}).split('/')[1]

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


def service_worker(request):
    """Serve the service worker at the site root so its scope is '/'.
    This makes pages like /practice-try/... installable (required by PWA install criteria).
    """
    from django.contrib.staticfiles import finders
    file_path = finders.find("js/service-worker.js") or finders.find("service-worker.js")
    if not file_path:
        return HttpResponse("// service worker not found", content_type="application/javascript", status=404)
    with open(file_path, "rb") as f:
        content = f.read()
    return HttpResponse(content, content_type="application/javascript")
