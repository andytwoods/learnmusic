import json
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.timezone import now
from django_htmx.http import HttpResponseClientRefresh

from notes import tools
from notes.forms import LearningScenarioForm
from notes.instruments import instrument_infos, instruments
from notes.models import LearningScenario, NoteRecordPackage, LevelChoices, InstrumentKeys, ClefChoices
from notes.tools import generate_notes, compile_notes_per_skilllevel

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
    context = {
        'learningscenarios': LearningScenario.objects.filter(user=request.user).order_by('-created'),
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
            instrument_name = form.cleaned_data['instrument_name']
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
        received = json.loads(request.body)
        notes_added = received['added']
        notes_removed = received['removed']
        ls.edit_notes(added=notes_added, removed=notes_removed)
        return JsonResponse({'success': True}, status=200)

    lowest_note, highest_note = tools.get_instrument_range(ls.instrument_name, LevelChoices.ADVANCED)

    all_notes = [str(note) for note in generate_notes(lowest_note=lowest_note, highest_note=highest_note)]

    context = {'notes': ls.notes[0:20], 'all_notes': all_notes}

    return render(request, 'notes/learningscenario_edit_vocab.html', context=context)


def common_context(instrument_name: str, clef: str, sound: bool):
    instrument_info = instrument_infos[instrument_name]
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
    serialised_notes = tools.generate_serialised_notes(instrument, level)

    instrument_info = instrument_infos[instrument]

    my_instruments = instrument_infos.keys()
    levels = instruments.get(instrument, {}).keys()

    context = {
        'learningscenario_id': PRACTICE_TRY,
        'progress': serialised_notes,
        'key': instrument_info['common_keys'][0],
        'transpose_key': key,
        'level': level,
        'sound': sound,
        'instrument': instrument,
        'levels': levels,
        'instruments': my_instruments,
        'clef': clef,
        'keys': [key[1] for key in InstrumentKeys.choices],
        'clefs': [clef[1] for clef in ClefChoices.choices],
    }

    context.update(common_context(instrument_name=instrument, clef=clef, sound=sound))

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
    package = NoteRecordPackage.objects.get(id=package_id)
    package.process_answers(json_data)

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
    if request.method == 'POST':
        serialised_notes = json.loads(request.body)
    else:
        serialised_notes = tools.generate_serialised_notes(instrument, level.capitalize())

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


def progress_data_view(request, learningscenario_id):
    # 1. Decide time range or grouping based on granularity
    #    For example, we might define an earliest date to group from:
    earliest_date = now() - timedelta(days=30)  # last 30 days as example

    # 2. Retrieve all NoteRecordPackage items for this user in that range
    #    (Or skip if you have a different approach)
    packages = NoteRecordPackage.objects.filter(
        learningscenario__id=learningscenario_id,
        created__gte=earliest_date
    )

    # 3. Aggregate the data
    #    We'll just show a made-up structure here. In reality, you’d:
    #    - parse the .log JSON,
    #    - compute average reaction time per day/week/month,
    #    - compute overall accuracy per day/week/month,
    #    - also group by note to create the "by_note" data

    over_time_labels = []
    over_time_accuracy = []
    over_time_reaction = []

    by_note_labels = []
    by_note_accuracy = []
    by_note_reaction = []

    # 3a. Example: we do some naive iteration (for MVP) over each package’s log
    #     and accumulate stats in dictionaries. This can be expensive if data is large.
    #     For real usage, consider storing aggregated summaries in the DB or using F expressions.

    # Pseudo-structures for grouping
    grouped_by_date = {}
    grouped_by_note = {}

    pkg: NoteRecordPackage
    for pkg in packages:
        # pkg.log might be a JSON field containing many record items
        if not pkg.log:
            continue
        for record in pkg.log:
            # record looks like:
            # {"note": "F", "octave": "3", "alter": "1",
            #  "reaction_time_log": [181],
            #  "correct": [false]}
            # ...
            note_name = f"{record['note']}{record['octave']}"
            if record['alter'] == '1':
                note_name += '#'
            elif record['alter'] == '-1':
                note_name += 'b'

            # For each attempt:
            attempts_count = len(record['correct'])
            # Count how many are correct
            correct_count = sum(record['correct'])
            # Reaction times: average if you like
            reaction_avg = 0
            if record['reaction_time_log']:
                reaction_avg = sum(record['reaction_time_log']) / len(record['reaction_time_log'])

            # 3a(i) group by date
            # For a real aggregator, you'd convert pkg.created_at to day/week/month
            date_key = pkg.created.strftime("%Y-%m-%d")  # daily grouping example

            if date_key not in grouped_by_date:
                grouped_by_date[date_key] = {
                    "sum_correct": 0,
                    "sum_total": 0,
                    "sum_reaction": 0,
                    "count_reaction": 0
                }

            grouped_by_date[date_key]["sum_correct"] += correct_count
            grouped_by_date[date_key]["sum_total"] += attempts_count
            grouped_by_date[date_key]["sum_reaction"] += sum(record['reaction_time_log'])
            grouped_by_date[date_key]["count_reaction"] += len(record['reaction_time_log'])

            # 3a(ii) group by note
            if note_name not in grouped_by_note:
                grouped_by_note[note_name] = {
                    "sum_correct": 0,
                    "sum_total": 0,
                    "sum_reaction": 0,
                    "count_reaction": 0
                }

            grouped_by_note[note_name]["sum_correct"] += correct_count
            grouped_by_note[note_name]["sum_total"] += attempts_count
            grouped_by_note[note_name]["sum_reaction"] += sum(record['reaction_time_log'])
            grouped_by_note[note_name]["count_reaction"] += len(record['reaction_time_log'])

    grouped_by_note_sorted = tools.sort_notes(grouped_by_note)
    # 3b. Turn grouped data into lists for Chart.js
    # Over time
    for date_key in sorted(grouped_by_date.keys()):
        over_time_labels.append(date_key)
        correct = grouped_by_date[date_key]["sum_correct"]
        total = grouped_by_date[date_key]["sum_total"]
        if total > 0:
            accuracy_pct = (correct / total) * 100
        else:
            accuracy_pct = 0
        over_time_accuracy.append(round(accuracy_pct, 1))

        if grouped_by_date[date_key]["count_reaction"] > 0:
            avg_reaction = (grouped_by_date[date_key]["sum_reaction"]
                            / grouped_by_date[date_key]["count_reaction"])
        else:
            avg_reaction = 0
        over_time_reaction.append(round(avg_reaction, 1))

    # By note
    # This is not time-based, just a sum across the whole period
    for note_key in grouped_by_note_sorted:
        by_note_labels.append(note_key)
        correct = grouped_by_note_sorted[note_key]["sum_correct"]
        total = grouped_by_note_sorted[note_key]["sum_total"]
        if total > 0:
            accuracy_pct = (correct / total) * 100
        else:
            accuracy_pct = 0
        by_note_accuracy.append(round(accuracy_pct, 1))

        if grouped_by_note_sorted[note_key]["count_reaction"] > 0:
            avg_reaction = (grouped_by_note_sorted[note_key]["sum_reaction"]
                            / grouped_by_note_sorted[note_key]["count_reaction"])
        else:
            avg_reaction = 0
        by_note_reaction.append(round(avg_reaction, 1))


    # Finally assemble JSON for the chart
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
