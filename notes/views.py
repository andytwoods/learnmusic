import json
from datetime import timedelta, datetime
from statistics import median  # Python 3.4+ has a built-in median function

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.http import JsonResponse
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
from notes.models import LearningScenario, NoteRecordPackage, NoteRecord, LevelChoices, InstrumentKeys, ClefChoices
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


def common_context(instrument_name: str, clef: str, sound: bool):
    """Build common context for practice views using a centralized resolver."""
    from notes.instrument_data import resolve_instrument

    canonical = resolve_instrument(instrument_name)
    if not canonical:
        from django.http import Http404
        raise Http404(f"Instrument not found: {instrument_name}")

    instrument_info = instrument_infos[canonical]

    if sound:
        instrument_template = 'notes/instruments/mic_input.html'
        score_css = 'justify-content-center'
    else:
        instrument_template = 'notes/instruments/' + instrument_info['answer_template']
        score_css = ''

    return {
        'answers_json': instrument_info['answers'],
        'instrument_template': instrument_template,
        'clef': clef.lower(),
        'instrument': canonical,
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
        'octave': learningscenario.octave_shift,
    }

    context.update(common_context(instrument_name=instrument_name, clef=package.learningscenario.clef, sound=sound))

    return render(request, 'notes/practice.html', context=context)


def practice_demo(request):
    url = reverse('practice-try',
                  kwargs={'instrument': 'trumpet',
                          'clef': 'treble',
                          'key': 'Bb',
                          'transpose': 'Bb',
                          'level': 'beginner',
                          'octave': 0})
    return redirect(url)

def practice_try_manifest(request, instrument: str, clef: str, key: str, transpose: str = "", level: str = "", octave: int = 0):
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

    # Generate start URL for this specific configuration (remove /manifest.json from the end)
    start_url = request.build_absolute_uri().replace('/manifest.json', '/')

    manifest_data = {
        "name": app_name,
        "short_name": f"{instrument.capitalize()} {level}",
        "description": f"Practice {instrument} reading in {clef} clef at {level} level",
        "start_url": start_url,
        "scope": "/",
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


def practice_try(request, instrument: str, clef: str, key: str, transpose: str = "", level: str = "", octave: int = 0, sound: bool = False):
    # Ensure instrument is properly capitalized
    # Handle POST request with progress data
    if request.method == 'POST':
        data = request.POST.get('save-to-cloud-btn')
        print(request.POST)

    if 'sharp' in key:
        key = key.replace('sharp', '#')
    elif 'flat' in key:
        key = key.replace('flat', 'b')

    if 'sharp' in transpose:
        transpose = transpose.replace('sharp', '#')
    elif 'flat' in transpose:
        transpose = transpose.replace('flat', 'b')

    # Slug-safe variants for URLs
    key_slug = key.replace('#', 'sharp').replace('b', 'flat') if key else ''
    transpose_slug = transpose.replace('#', 'sharp').replace('b', 'flat') if transpose else ''

    from notes.instrument_data import resolve_instrument
    canonical_instrument = resolve_instrument(instrument)
    if not canonical_instrument:
        from django.http import Http404
        raise Http404(f"Instrument not found: {instrument}")

    # Handle GET request
    serialised_notes = tools.generate_serialised_notes(canonical_instrument, level)

    instrument_info = instrument_infos[canonical_instrument]

    my_instruments = instrument_infos.keys()
    levels = instruments.get(canonical_instrument, {}).keys()

    context = {
        'learningscenario_id': PRACTICE_TRY,
        'progress': serialised_notes,
        'key': key.capitalize() if key else instrument_info['common_keys'][0],
        'transpose_key': transpose.capitalize() if transpose else '',
        'level': level,
        'sound': sound,
        'instrument': canonical_instrument,  # Canonical instrument name for consistency
        'levels': levels,
        'instruments': my_instruments,
        'clef': clef,
        'instrument_defaults': get_instrument_defaults(),
        'keys': [key[1] for key in InstrumentKeys.choices],
        'clefs': [clef[1] for clef in ClefChoices.choices],
        'octaves': ['2', '1', '0', '-1', '-2'],
        'octave': octave,
        # Add original key for manifest URL generation
        'original_key': key,  # already formatted with #/b above
                'original_key_slug': key_slug,
                'transpose_key_slug': transpose_slug,
    }

    context.update(common_context(instrument_name=canonical_instrument, clef=clef, sound=sound))

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
    from notes.instrument_data import resolve_instrument
    canonical_instrument = resolve_instrument(instrument)
    if not canonical_instrument:
        from django.http import Http404
        raise Http404(f"Instrument not found: {instrument}")

    if request.method == 'POST':
        serialised_notes = json.loads(request.body)
    else:
        serialised_notes = tools.generate_serialised_notes(canonical_instrument, level.capitalize())

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
    try:
        return render(request, 'notes/htmx/_reminder_settings_button.html')
    except Exception as e:
        # If there's an error, provide a simple button that will still work
        print(f"Error in reminder_settings_button: {str(e)}")
        html = """
        <button class="btn btn-success btn-lg mt-3" hx-get="/reminder-settings-form/" hx-target="#reminder-settings-container" hx-swap="innerHTML" hx-no-confirm='true'>
          <i class="fas fa-bell"></i> Reminder settings
        </button>
        """
        return HttpResponse(html)


@login_required
def reminder_settings_form(request):
    """
    Renders the reminder settings form HTMX fragment.

    This view converts the reminder time from UTC (as stored in the database) to the user's
    local timezone for display in the form. This ensures that users see the reminder time
    in their own timezone, even though it's stored in UTC in the database.
    """
    try:
        # Get the user's current reminder settings
        user = request.user
        profile = user.profile  # This will create a profile if it doesn't exist
        utc_reminder_time = profile.reminder_time
        current_timezone = profile.timezone

        # Check if reminders are disabled
        reminders_disabled = utc_reminder_time == "DISABLED"

        # If reminders are disabled, set a default time for the form
        if reminders_disabled:
            local_reminder_time = "18:00"  # Default to 6 PM if reminders are disabled
        else:
            try:
                # Convert the UTC time to the user's local timezone
                # Parse the UTC time (HH:MM)
                hour, minute = map(int, utc_reminder_time.split(':'))

                # Create a datetime object for today at the specified time in UTC
                utc_tz = ZoneInfo("UTC")
                now = datetime.now(utc_tz)
                utc_dt = datetime(now.year, now.month, now.day, hour, minute, tzinfo=utc_tz)

                # Convert to the user's timezone
                user_tz = ZoneInfo(current_timezone)
                local_dt = utc_dt.astimezone(user_tz)

                # Format as HH:MM
                local_reminder_time = local_dt.strftime("%H:%M")
            except Exception as e:
                # If there's an error with timezone conversion, use the UTC time directly
                local_reminder_time = utc_reminder_time
                # Log the error for debugging
                print(f"Error converting timezone: {str(e)}")

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
        try:
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
        except Exception as e:
            # If there's an error with timezone handling, use the common timezones only
            all_timezones = common_timezones
            # Log the error for debugging
            print(f"Error processing timezones: {str(e)}")

        context = {
            'reminder_time': local_reminder_time,
            'current_timezone': current_timezone,
            'timezones': all_timezones,
            'reminders_disabled': reminders_disabled,
        }

        return render(request, 'notes/htmx/_reminder_settings_form.html', context)
    except Exception as e:
        # If there's an error, provide a simplified form with minimal functionality
        print(f"Error in reminder_settings_form: {str(e)}")
        context = {
            'reminder_time': "18:00",  # Default to 6 PM
            'current_timezone': "UTC",
            'timezones': [('UTC', 'UTC')],  # Only provide UTC as an option
            'reminders_disabled': False,
            'error_message': "There was an error loading your reminder settings. Using default values."
        }
        return render(request, 'notes/htmx/_reminder_settings_form.html', context)


@login_required
def reminder_settings_submit(request):
    """
    Handles the submission of the reminder settings form.

    This view converts the reminder time from the user's local timezone to UTC before saving
    it to the database. This ensures that all reminder times are stored in a consistent timezone
    (UTC) in the database, regardless of the user's local timezone. The user's timezone is still
    stored for display purposes, but the actual reminder time is in UTC.
    """
    try:
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
                local_reminder_time = request.POST.get('reminder_time')
                user_timezone = request.POST.get('timezone')

                # Save the timezone to the user's profile
                user = request.user
                profile = user.profile  # This will create a profile if it doesn't exist

                # Only convert the time if it's not disabled
                if local_reminder_time != "DISABLED":
                    try:
                        # Convert the reminder time from local timezone to UTC
                        # Parse the local time (HH:MM)
                        hour, minute = map(int, local_reminder_time.split(':'))

                        # Create a datetime object for today at the specified time in the user's timezone
                        user_tz = ZoneInfo(user_timezone)
                        now = datetime.now(user_tz)
                        local_dt = datetime(now.year, now.month, now.day, hour, minute, tzinfo=user_tz)

                        # Convert to UTC
                        utc_dt = local_dt.astimezone(ZoneInfo("UTC"))

                        # Format as HH:MM
                        utc_reminder_time = utc_dt.strftime("%H:%M")

                        # Save the UTC time
                        profile.reminder_time = utc_reminder_time
                    except Exception as e:
                        # If there's an error with timezone conversion, use the local time directly
                        profile.reminder_time = local_reminder_time
                        # Log the error for debugging
                        print(f"Error converting timezone in submit: {str(e)}")
                else:
                    profile.reminder_time = local_reminder_time

                profile.timezone = user_timezone
                profile.save()

            # Return the reminder settings button
            return render(request, 'notes/htmx/_reminder_settings_button.html')

        # If not a POST request, redirect to the form
        return redirect('reminder-settings-form')
    except Exception as e:
        # If there's an error, provide a helpful error message
        print(f"Error in reminder_settings_submit: {str(e)}")
        context = {
            'error_message': "There was an error saving your reminder settings. Please try again.",
            'reminder_time': request.POST.get('reminder_time', "18:00"),
            'current_timezone': request.POST.get('timezone', "UTC"),
            'timezones': [('UTC', 'UTC')],  # Only provide UTC as an option
            'reminders_disabled': False
        }
        return render(request, 'notes/htmx/_reminder_settings_form.html', context)


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


@login_required
def reminders(request):
    """
    View to display and manage user's active subscriptions.
    Shows all LearningScenarios where reminder_type is not NONE.
    Allows unsubscribing from PUSH and EMAIL notifications.
    Also provides an option to unsubscribe from all notifications at once.
    """
    if request.method == 'POST':
        # Handle unsubscribe actions
        scenario_id = request.POST.get('scenario_id')
        action = request.POST.get('action')

        # Handle unsubscribe all action
        if action == 'unsubscribe_all':
            # Get all active subscriptions for the user
            active_subscriptions = LearningScenario.objects.filter(
                user=request.user
            ).exclude(
                reminder_type=LearningScenario.Reminder.NONE
            )

            # Update all to NONE
            count = active_subscriptions.count()
            active_subscriptions.update(reminder_type=LearningScenario.Reminder.NONE)

            if count > 0:
                messages.success(request, f"Successfully unsubscribed from all {count} notifications.")
            else:
                messages.info(request, "No active subscriptions to unsubscribe from.")

            return redirect('reminders')

        # Handle individual unsubscribe actions
        elif scenario_id and action:
            try:
                scenario = LearningScenario.objects.get(id=scenario_id, user=request.user)

                # Update reminder_type based on the action
                if action == 'unsubscribe_push':
                    if scenario.reminder_type == LearningScenario.Reminder.ALL:
                        scenario.reminder_type = LearningScenario.Reminder.EMAIL
                    elif scenario.reminder_type == LearningScenario.Reminder.PUSH_NOTIFICATION:
                        scenario.reminder_type = LearningScenario.Reminder.NONE

                elif action == 'unsubscribe_email':
                    if scenario.reminder_type == LearningScenario.Reminder.ALL:
                        scenario.reminder_type = LearningScenario.Reminder.PUSH_NOTIFICATION
                    elif scenario.reminder_type == LearningScenario.Reminder.EMAIL:
                        scenario.reminder_type = LearningScenario.Reminder.NONE

                scenario.save()
                messages.success(request, "Subscription updated successfully.")
            except LearningScenario.DoesNotExist:
                messages.error(request, "Learning scenario not found.")

        # Redirect to the same page to refresh the content
        return redirect('reminders')

    # Get all active subscriptions (reminder_type is not NONE)
    active_subscriptions = LearningScenario.objects.filter(
        user=request.user
    ).exclude(
        reminder_type=LearningScenario.Reminder.NONE
    ).order_by('-created')

    context = {
        'active_subscriptions': active_subscriptions,
    }

    return render(request, 'notes/reminders.html', context)

@require_POST
def cache_to_backend(request):
    print(request.POST)
    return JsonResponse({}, status=200)
