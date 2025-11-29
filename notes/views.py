import json
from datetime import timedelta, datetime
from statistics import median  # Python 3.4+ has a built-in median function

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.timezone import now
from django.views.decorators.http import require_POST
from django_htmx.http import HttpResponseClientRefresh
from zoneinfo import available_timezones, ZoneInfo

from pushover_complete import PushoverAPI

from notes import tools
from notes.forms import LearningScenarioForm
from notes.instrument_data import instrument_infos, instruments, get_instrument_defaults
from notes.models import LearningScenario, NoteRecordPackage, LevelChoices, InstrumentKeys, ClefChoices, \
    BlankAbsolutePitch, FIFTHS_TO_VEXFLOW_MAJOR
from notes.tools import generate_notes, compile_notes_per_skilllevel, convert_note_slash_to_db, toCamelCase

PRACTICE_TRY = 'practice-try'


@login_required
def notes_home(request):
    if request.htmx:
        action = request.POST.get('action')
        if action == 'delete':
            learningscenario_id = request.POST.get('id')
            LearningScenario.objects.get(id=learningscenario_id).delete()
        elif action == 'copy':
            learningscenario_id = request.POST.get('id')
            LearningScenario.objects.get(id=learningscenario_id).clone()
            return HttpResponseClientRefresh()
        else:
            raise Exception("unknown action")
        return HttpResponse('', status=200)

    # Get all learning scenarios for the user
    learningscenarios = LearningScenario.objects.filter(user=request.user).order_by('-created')

    LearningScenario.add_history(learningscenarios)

    # Get the VAPID public key from settings for push notifications
    from django.conf import settings

    # The VAPID public key is already in URL-safe base64 format in the .env file
    # Pass it directly to the template without additional encoding
    context = {
        'learningscenarios': learningscenarios,
    }
    return render(request, 'notes/learning_home.html', context=context)


@login_required
def new_learningscenario(request):
    scenario = LearningScenario(user=request.user)
    scenario.save()
    url = reverse('edit-learning-scenario', kwargs={'pk': scenario.id})
    return redirect(url + '?new=true')


@login_required
def edit_learningscenario(request, pk: int):
    model = LearningScenario.objects.get(id=pk)
    form = None
    if request.POST:
        form = LearningScenarioForm(request.POST, instance=model, request=request)
        if form.is_valid():
            ls: LearningScenario = form.save(commit=False)
            ls.save()
            return redirect(reverse('notes-home'))

    if not form:
        form = LearningScenarioForm(instance=model, request=request)

    context = {'form': form,
               'learningscenario_pk': model.pk,
               'instruments_info': instrument_infos,
               'new': request.GET.get('new', False), }

    return render(request, 'notes/learningscenario_edit.html', context=context)


@login_required
def edit_learningscenario_notes(request, pk: int):
    ls: LearningScenario = LearningScenario.objects.get(id=pk)

    # not sure why request.POST does not suffice. Perhaps cos JSON sent
    if request.method == 'POST':
        received = json.loads(request.POST.get('data'))
        notes_added = [convert_note_slash_to_db(note) for note in received['added']]
        notes_removed = [convert_note_slash_to_db(note) for note in received['removed']]
        ls.edit_notes(added=notes_added, removed=notes_removed, commit=True)
        messages.success(request, 'Notes updated')

    lowest_note, highest_note = tools.get_instrument_range(ls.instrument_name, LevelChoices.ADVANCED)

    all_notes = [str(note) for note in generate_notes(lowest_note=lowest_note, highest_note=highest_note)]

    context = {'notes': ls.notes[0:20], 'all_notes': all_notes}

    return render(request, 'notes/learningscenario_edit_vocab.html', context=context)


def common_context(instrument_name: str, clef: str, sound: bool | None = None):
    """Build common context for practice views using a centralized resolver.

    The optional `sound` parameter is accepted for backward compatibility with existing callers/tests.
    """
    from notes.instrument_data import resolve_instrument

    canonical = resolve_instrument(instrument_name)
    if not canonical:
        from django.http import Http404
        raise Http404(f"Instrument not found: {instrument_name}")

    instrument_info = instrument_infos[canonical]

    instrument_template = 'notes/instruments/' + instrument_info['answer_template']
    score_css = ''

    return {
        'answers_json': instrument_info['answers'],
        'instrument_template': instrument_template,
        'clef': clef.lower(),
        'instrument': canonical,
        'score_css': score_css,
        'response_count': 30,
    }


def practice(request, learningscenario_id: int, sound: bool = False):
    package, serialised_notes = LearningScenario.progress_latest_serialised(learningscenario_id)

    instrument_name: str = package.learningscenario.instrument_name
    learningscenario: LearningScenario = LearningScenario.objects.get(id=learningscenario_id)
    context = {
        'learningscenario_id': learningscenario_id,
        'ux': learningscenario.ux,
        'package_id': package.id,
        'key': learningscenario.relative_key,
        'progress': serialised_notes,
        'sound': sound,
        'absolute_pitch': learningscenario.get_absolute_pitch(),
        'level': learningscenario.level.lower(),
        'octave': learningscenario.octave_shift,
    }

    context.update(common_context(instrument_name=instrument_name, clef=package.learningscenario.clef, sound=sound))

    return render(request, 'notes/practice.html', context=context)


def practice_demo(request):
    url = reverse('practice-try-sigs-abs',
                  kwargs={'instrument': 'trumpet',
                          'clef': 'treble',
                          'key': 'Bb',
                          'absolute_pitch': 'Bb',
                          'level': 'beginner',
                          'octave': 0,
                          'signatures': '0'})
    return redirect(url)


def practice_try_manifest(request, instrument: str, clef: str, key: str, absolute_pitch: str = "", level: str = "",
                          octave: int = 0, signatures: str = ""):
    """Generate dynamic PWA manifest for practice-try pages"""
    # Handle key formatting for display
    display_key = key
    if 'sharp' in key:
        display_key = key.replace('sharp', '#')
    elif 'flat' in key:
        display_key = key.replace('flat', 'b')

    # Create dynamic app name based on parameters
    app_name = f"{instrument.capitalize()} Practice - {level.capitalize()}"
    if display_key and display_key != instrument.capitalize():
        app_name += f" ({display_key})"

    # Generate a stable app identity and start URL for this specific configuration
    # Use path-relative values to avoid treating different hosts as different apps
    base_path = request.path.replace('/manifest.json', '/')
    # Per Web App Manifest spec, set a stable id so Android doesn't treat updates as a new app
    app_id = base_path  # path-scoped id is stable per practice configuration
    # Start URL should be within scope and preferably relative
    start_url = base_path

    manifest_data = {
        "name": app_name,
        "short_name": f"{instrument.capitalize()} {level}",
        "description": f"Practice {instrument} reading in {clef} clef at {level} level",
        "id": app_id,
        "start_url": start_url,
        # Restrict scope to this practice configuration so the app identity remains stable
        "scope": base_path,
        "display": "standalone",
        "orientation": "any",
        "background_color": "#ffffff",
        "theme_color": "#007bff",
        "icons": [
            {
                "src": "/static/favicon/android-chrome-192x192.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any maskable"
            },
            {
                "src": "/static/favicon/android-chrome-512x512.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any maskable"
            }
        ]
    }

    return JsonResponse(manifest_data)


def practice_try(request, instrument: str, clef: str, key: str, absolute_pitch: str = "", level: str = "",
                 octave: int = 0, signatures: str = ""):
    # Ensure instrument is properly capitalized
    # Handle POST request with progress data

    if request.method == 'POST':
        data = request.POST.get('save-to-cloud-btn')
        print(request.POST)

    # Normalize and compute slug-safe variants
    key, key_slug = tools.normalize_and_slug(key)
    absolute_pitch, absolute_pitch_slug = tools.normalize_and_slug(absolute_pitch)

    selected_signatures = tools.compute_signatures(signatures)

    from notes.instrument_data import resolve_instrument
    canonical_instrument = resolve_instrument(instrument)
    if not canonical_instrument:
        from django.http import Http404
        raise Http404(f"Instrument not found: {instrument}")

    try:
        serialised_notes = tools.generate_serialised_notes(canonical_instrument, level)
    except KeyError:
        from django.http import Http404
        raise Http404

    instrument_info = instrument_infos[canonical_instrument]

    my_instruments = instrument_infos.keys()
    levels = instruments.get(canonical_instrument, {}).keys()

    # Build progress wrapper with signatures for practice_try
    progress_wrapped = {
        'notes': serialised_notes,
        'signatures': {
            'fifths': selected_signatures,
            'vexflow': [FIFTHS_TO_VEXFLOW_MAJOR[s] for s in selected_signatures],
        }
    }

    context = {
        'learningscenario_id': PRACTICE_TRY,
        'progress': progress_wrapped,
        'key': key.capitalize() if key else instrument_info['common_keys'][0],
        'absolute_pitch': absolute_pitch.capitalize() if absolute_pitch else '',
        'level': level,
        'instrument': canonical_instrument,  # Canonical instrument name for consistency
        'levels': levels,
        'instruments': my_instruments,
        'clef': clef,
        'instrument_defaults': get_instrument_defaults(),
        'keys': [key[1] for key in InstrumentKeys.choices],
        'clefs': [clef[1] for clef in ClefChoices.choices],
        'octaves': ['3', '2', '1', '0', '-1', '-2', '-3', ],
        'octave': octave,
        # Add original key for manifest URL generation
        'original_key': key,  # already formatted with #/b above
        'original_key_slug': key_slug,
        'absolute_pitch_slug': absolute_pitch_slug,
        # Signatures context
        'signatures': list(range(-7, 8)),
        'signatures_with_names': [(s, FIFTHS_TO_VEXFLOW_MAJOR[s]) for s in range(0, -8, -1)] +
                                 [(s, FIFTHS_TO_VEXFLOW_MAJOR[s]) for s in range(1, 8)],
        # [(s, FIFTHS_TO_VEXFLOW_MAJOR[s]) for s in range(-1, -8, -1)], # This code gives range(-1, -8)
        'selected_signatures': selected_signatures,
        'signatures_slug': ','.join(str(s) for s in selected_signatures),
    }

    context.update(common_context(instrument_name=canonical_instrument, clef=clef))

    rt_per_sl = compile_notes_per_skilllevel([{'note': n['note'], 'alter': n['alter'], 'octave': n['octave']}
                                              for n in serialised_notes])
    graph_context = {
        'progress': progress_wrapped,
        'rt_per_sk': rt_per_sl,
    }
    context.update(graph_context)

    return render(request, 'notes/practice_try.html', context=context)


@login_required
def practice_data(request, package_id: int):
    json_data = json.loads(request.body)
    package: NoteRecordPackage = NoteRecordPackage.objects.get(id=package_id)
    package.add_result(json_data)
    return JsonResponse({'success': True})








def progress_data_view(request, learningscenario_id):
    # 1. Decide the time window
    earliest_date = now() - timedelta(days=30)  # last 30 days as example

    # 2. Retrieve all NoteRecordPackage items for this learning scenario in that range
    packages = NoteRecordPackage.objects.filter(
        learningscenario__id=learningscenario_id,
        created__gte=earliest_date
    )

    # 3. Prepare structures for grouping stats
    over_time_labels = []
    over_time_accuracy = []
    over_time_reaction = []

    by_note_labels = []
    by_note_accuracy = []
    by_note_reaction = []

    # Instead of sum/count for reaction times, keep a list of all reaction times
    grouped_by_date = {}
    grouped_by_note = {}

    for package in packages:
        date_key = package.created.strftime("%Y-%m-%d")
        # Initialize date bucket
        if date_key not in grouped_by_date:
            grouped_by_date[date_key] = {
                "sum_correct": 0,
                "sum_total": 0,
                "reaction_times": []
            }
        # Skip if no log
        if not isinstance(package.log, list):
            continue
        # Iterate over each note item in the package log
        for item in package.log:
            note_name = f"{item.get('note', '')}{item.get('octave', '')}"
            alter = item.get('alter')
            if alter == '1':
                note_name += '#'
            elif alter == '-1':
                note_name += 'b'
            # Ensure note bucket exists
            if note_name not in grouped_by_note:
                grouped_by_note[note_name] = {
                    "sum_correct": 0,
                    "sum_total": 0,
                    "reaction_times": []
                }
            correct_list = item.get('correct', []) or []
            rt_list = item.get('reaction_time_log', []) or []
            # Use paired data points only
            n = min(len(correct_list), len(rt_list)) if (correct_list and rt_list) else len(rt_list)
            for i in range(n):
                grouped_by_date[date_key]["sum_total"] += 1
                if i < len(correct_list) and correct_list[i]:
                    grouped_by_date[date_key]["sum_correct"] += 1
                grouped_by_date[date_key]["reaction_times"].append(int(rt_list[i]) if rt_list[i] is not None else 0)

                grouped_by_note[note_name]["sum_total"] += 1
                if i < len(correct_list) and correct_list[i]:
                    grouped_by_note[note_name]["sum_correct"] += 1
                grouped_by_note[note_name]["reaction_times"].append(int(rt_list[i]) if rt_list[i] is not None else 0)

    # Optionally, if you need a custom-sorted approach to notes
    grouped_by_note_sorted = tools.sort_notes(grouped_by_note)

    # 3b. Convert grouped data into lists for Chart.js
    # Over time
    for date_key in sorted(grouped_by_date.keys()):
        over_time_labels.append(date_key)
        correct = grouped_by_date[date_key]["sum_correct"]
        total = grouped_by_date[date_key]["sum_total"]

        # Accuracy is still sum(correct)/sum(total)
        if total > 0:
            accuracy_pct = (correct / total) * 100
        else:
            accuracy_pct = 0
        over_time_accuracy.append(round(accuracy_pct, 1))

        # Reaction time is now the median of all reaction times recorded that day
        reaction_times = grouped_by_date[date_key]["reaction_times"]
        if reaction_times:
            med_reaction = median(reaction_times)
        else:
            med_reaction = 0
        over_time_reaction.append(round(med_reaction, 1))

    # By note
    for note_key in grouped_by_note_sorted:
        by_note_labels.append(note_key)

        correct = grouped_by_note_sorted[note_key]["sum_correct"]
        total = grouped_by_note_sorted[note_key]["sum_total"]

        # Accuracy
        if total > 0:
            accuracy_pct = (correct / total) * 100
        else:
            accuracy_pct = 0
        by_note_accuracy.append(round(accuracy_pct, 1))

        # Median reaction time per note
        reaction_times = grouped_by_note_sorted[note_key]["reaction_times"]
        if reaction_times:
            med_reaction = median(reaction_times)
        else:
            med_reaction = 0
        by_note_reaction.append(round(med_reaction, 1))

    # Assembling JSON for Chart.js
    data = {
        "over_time": {
            "labels": over_time_labels,
            "accuracy": over_time_accuracy,
            "reaction_time": over_time_reaction
        },
        "by_note": {
            "labels": by_note_labels,
            "accuracy": by_note_accuracy,
            "reaction_time": by_note_reaction
        }
    }

    return JsonResponse(data, safe=True)


@login_required
def pushover_callback(request):
    user_key = request.GET.get("pushover_user_key")
    if user_key:
        request.user.pushover_key = user_key
        request.user.save()

        p = PushoverAPI(settings.PUSHOVER_APP_TOKEN)
        p.send_message(user_key, message="Thanks for subscribing!", title="Subscription successful")

    if request.GET.get('pushover_unsubscribed_user_key', None):
        request.user.pushover_key = ''
        request.user.save()
        messages.success(request, 'You have been unsubscribed from push notifications.')

    return redirect(reverse('notes-home'))




