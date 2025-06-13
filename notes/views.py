import json
from datetime import timedelta, datetime
from statistics import median  # Python 3.4+ has a built-in median function

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.timezone import now
from django_htmx.http import HttpResponseClientRefresh
from zoneinfo import available_timezones, ZoneInfo

from notes import tools
from notes.forms import LearningScenarioForm
from notes.instrument_data import instrument_infos, instruments
from notes.models import LearningScenario, NoteRecordPackage, NoteRecord, LevelChoices, InstrumentKeys, ClefChoices
from notes.tools import generate_notes, compile_notes_per_skilllevel, convert_note_slash_to_db

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
        form = LearningScenarioForm(request.POST, instance=model)
        if form.is_valid():
            ls: LearningScenario = form.save(commit=False)
            ls.save()
            return redirect(reverse('notes-home'))

    if not form:
        form = LearningScenarioForm(instance=model)

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


def common_context(instrument_name: str, clef: str, sound: bool):
    # Ensure instrument_name is properly capitalized
    capitalized_instrument = instrument_name.capitalize() if instrument_name else instrument_name
    instrument_info = instrument_infos[capitalized_instrument]
    if sound:
        instrument_template = 'notes/instruments/mic_input.html'
        score_css = 'justify-content-center'
    else:
        instrument_template = 'notes/instruments/' + instrument_info['answer_template']
        score_css = ''

    return {'answers_json': instrument_info['answers'],
            'instrument_template': instrument_template,
            'clef': clef.lower(),
            'instrument': instrument_name,
            'score_css': score_css,
            }


@login_required
def practice(request, learningscenario_id: int, sound: bool = False):
    package, serialised_notes = LearningScenario.progress_latest_serialised(learningscenario_id)

    instrument_name: str = package.learningscenario.instrument_name
    learningscenario: LearningScenario = LearningScenario.objects.get(id=learningscenario_id)
    context = {
        'learningscenario_id': learningscenario_id,
        'ux': learningscenario.ux,
        'package_id': package.id,
        'key': learningscenario.key,
        'progress': serialised_notes,
        'sound': sound,
        'transpose_key': learningscenario.get_transposeKey(),
        'level': learningscenario.level.lower(),
    }

    context.update(common_context(instrument_name=instrument_name, clef=package.learningscenario.clef, sound=sound))

    return render(request, 'notes/practice.html', context=context)


def practice_try(request, instrument: str, clef: str, key: str, level: str, sound: bool = False):
    # Ensure instrument is properly capitalized
    capitalized_instrument = instrument.capitalize() if instrument else instrument

    serialised_notes = tools.generate_serialised_notes(capitalized_instrument, level)

    instrument_info = instrument_infos[capitalized_instrument]

    my_instruments = instrument_infos.keys()
    levels = instruments.get(capitalized_instrument, {}).keys()

    context = {
        'learningscenario_id': PRACTICE_TRY,
        'progress': serialised_notes,
        'key': instrument_info['common_keys'][0],
        'transpose_key': key.capitalize() if key else '',
        'level': level,
        'sound': sound,
        'instrument': capitalized_instrument,  # Use capitalized instrument name for consistency
        'levels': levels,
        'instruments': my_instruments,
        'clef': clef,
        'keys': [key[1] for key in InstrumentKeys.choices],
        'clefs': [clef[1] for clef in ClefChoices.choices],
    }

    context.update(common_context(instrument_name=capitalized_instrument, clef=clef, sound=sound))

    rt_per_sl = compile_notes_per_skilllevel([{'note': n['note'], 'alter': n['alter'], 'octave': n['octave']}
                                              for n in serialised_notes])
    graph_context = {
        'progress': serialised_notes,
        'rt_per_sk': rt_per_sl,
    }
    context.update(graph_context)

    return render(request, 'notes/practice_try.html', context=context)


@login_required
def practice_data(request, package_id: int):
    json_data = json.loads(request.body)
    package: NoteRecordPackage = NoteRecordPackage.objects.get(id=package_id)
    package.add_result(json_data)

    noterecord: NoteRecord = NoteRecord(
        learningscenario=package.learningscenario,
        note=json_data.get('note', ''),
        alter=json_data.get('alter', ''),
        octave=json_data.get('octave', ''),
        reaction_time=json_data.get('reaction_time', 0),
        correct=json_data.get('correct', False)
    )
    noterecord.save()


    return JsonResponse({'success': True})


@login_required
def learningscenario_graph(request, learningscenario_id):
    package, serialised_notes = LearningScenario.progress_latest_serialised(learningscenario_id)

    rt_per_sl = compile_notes_per_skilllevel([{'note': n['note'], 'alter': n['alter'], 'octave': n['octave']}
                                              for n in serialised_notes])

    context = {
        'learningscenario_id': learningscenario_id,
        # 'package_id': package.id,
        'package': package,
        'progress': serialised_notes,
        'rt_per_sk': rt_per_sl,
    }

    return render(request, 'notes/learningscenario_graph.html', context=context)


def learningscenario_graph_try(request, instrument: str, level: str):
    # Ensure instrument is properly capitalized
    capitalized_instrument = instrument.capitalize() if instrument else instrument

    if request.method == 'POST':
        serialised_notes = json.loads(request.body)
    else:
        serialised_notes = tools.generate_serialised_notes(capitalized_instrument, level.capitalize())

    rt_per_sl = compile_notes_per_skilllevel([{'note': n['note'], 'alter': n['alter'], 'octave': n['octave']}
                                              for n in serialised_notes])
    context = {
        'package': None,
        'progress': serialised_notes,
        'rt_per_sk': rt_per_sl,
    }

    return render(request, 'notes/learningscenario_graph_try.html', context=context)


@login_required
def progress(request, learningscenario_id: int):
    context = {
        'learningscenario_id': learningscenario_id,
        'learningscenario': LearningScenario.objects.get(id=learningscenario_id),
    }
    return render(request, 'progress.html', context=context)


@login_required
def reminder_settings_button(request):
    """
    Renders the reminder settings button HTMX fragment.
    """
    return render(request, 'notes/htmx/_reminder_settings_button.html')


@login_required
def reminder_settings_form(request):
    """
    Renders the reminder settings form HTMX fragment.
    """
    # Get the user's current reminder settings
    user = request.user
    profile = user.profile  # This will create a profile if it doesn't exist
    reminder_time = profile.reminder_time
    current_timezone = profile.timezone

    # Check if reminders are disabled
    reminders_disabled = reminder_time == "DISABLED"

    # If reminders are disabled, set a default time for the form
    if reminders_disabled:
        reminder_time = "18:00"  # Default to 6 PM if reminders are disabled

    # Create a list of common timezones for the form
    common_timezones = [
        ('UTC', 'UTC'),
        ('US/Pacific', 'US/Pacific'),
        ('US/Mountain', 'US/Mountain'),
        ('US/Central', 'US/Central'),
        ('US/Eastern', 'US/Eastern'),
        ('Europe/London', 'Europe/London'),
        ('Europe/Berlin', 'Europe/Berlin'),
        ('Europe/Paris', 'Europe/Paris'),
        ('Asia/Tokyo', 'Asia/Tokyo'),
        ('Australia/Sydney', 'Australia/Sydney'),
    ]

    # Add all available timezones as options with UTC offset in hours
    all_timezones = []
    now_utc = datetime.now(ZoneInfo("UTC"))

    for tz_name in available_timezones():
        try:
            # Calculate the UTC offset in hours
            now_tz = now_utc.astimezone(ZoneInfo(tz_name))
            offset_seconds = now_tz.utcoffset().total_seconds()
            offset_hours = offset_seconds / 3600

            # Format the offset as +/-HH:MM
            sign = "+" if offset_hours >= 0 else "-"
            abs_offset = abs(offset_hours)
            offset_str = f"{sign}{int(abs_offset):02d}:{int((abs_offset % 1) * 60):02d}"

            # Create the display text with timezone name and UTC offset
            display_text = f"{tz_name} (UTC{offset_str})"

            all_timezones.append((tz_name, display_text))
        except Exception as e:
            # If there's an error with a timezone, just use the name without offset
            all_timezones.append((tz_name, tz_name))

    # Sort timezones by UTC offset
    all_timezones.sort(key=lambda x: now_utc.astimezone(ZoneInfo(x[0])).utcoffset().total_seconds())

    context = {
        'reminder_time': reminder_time,
        'current_timezone': current_timezone,
        'timezones': all_timezones,
        'reminders_disabled': reminders_disabled,
    }

    return render(request, 'notes/htmx/_reminder_settings_form.html', context)


@login_required
def reminder_settings_submit(request):
    """
    Handles the submission of the reminder settings form.
    """
    if request.method == 'POST':
        # Check if the user is removing reminders
        if request.POST.get('remove_reminders') == 'true':
            # Save special values to indicate reminders are disabled
            user = request.user
            profile = user.profile
            profile.reminder_time = "DISABLED"
            profile.save()
        else:
            # Normal save operation
            reminder_time = request.POST.get('reminder_time')
            timezone = request.POST.get('timezone')

            # Save the settings to the user's profile
            user = request.user
            profile = user.profile  # This will create a profile if it doesn't exist
            profile.reminder_time = reminder_time
            profile.timezone = timezone
            profile.save()

        # Return the reminder settings button
        return render(request, 'notes/htmx/_reminder_settings_button.html')

    # If not a POST request, redirect to the form
    return redirect('reminder-settings-form')


def progress_data_view(request, learningscenario_id):
    # 1. Decide the time window
    earliest_date = now() - timedelta(days=30)  # last 30 days as example

    # 2. Retrieve all NoteRecord items for this learning scenario in that range
    note_records = NoteRecord.objects.filter(
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

    for record in note_records:
        # Format note name
        note_name = f"{record.note}{record.octave}"
        if record.alter == '1':
            note_name += '#'
        elif record.alter == '-1':
            note_name += 'b'

        date_key = record.created.strftime("%Y-%m-%d")  # daily grouping example

        # Initialize dictionaries if not present
        if date_key not in grouped_by_date:
            grouped_by_date[date_key] = {
                "sum_correct": 0,
                "sum_total": 0,
                "reaction_times": []  # store all reaction times here
            }

        # Update date-based stats
        grouped_by_date[date_key]["sum_total"] += 1
        if record.correct:
            grouped_by_date[date_key]["sum_correct"] += 1
        grouped_by_date[date_key]["reaction_times"].append(record.reaction_time)

        # Initialize note-based stats if needed
        if note_name not in grouped_by_note:
            grouped_by_note[note_name] = {
                "sum_correct": 0,
                "sum_total": 0,
                "reaction_times": []
            }

        # Update note-based stats
        grouped_by_note[note_name]["sum_total"] += 1
        if record.correct:
            grouped_by_note[note_name]["sum_correct"] += 1
        grouped_by_note[note_name]["reaction_times"].append(record.reaction_time)

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
