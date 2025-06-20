from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.conf import settings
import os

from notes.instrument_data import instruments, instrument_infos


def home(request):
    # I broke the homepage when randomly updating the url to practice-try...
    # I don't want to repeat this mistake
    practice_url = reverse('practice-try', kwargs={
        'instrument': 'dummy',
        'key': 'dummy',
        'clef': 'dummy',
        'level': 'dummy'}).split('/')[1]

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
    """
    Serve the service worker from the root URL with the appropriate headers.
    This allows the service worker to have a scope of '/' even though it's
    physically located in the static directory.
    """
    # Path to the service worker file in the static directory
    sw_path = os.path.join(settings.STATICFILES_DIRS[0], 'service-worker.js')

    # Read the service worker file
    with open(sw_path, 'rb') as f:
        content = f.read()

    # Create a response with the service worker content
    response = HttpResponse(content, content_type='application/javascript')

    # Add the Service-Worker-Allowed header to allow the service worker to control the entire site
    response['Service-Worker-Allowed'] = '/'

    return response
