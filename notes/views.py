import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse

from notes.forms import LearningScenarioForm
from notes.instruments import instrument_infos
from notes.models import LearningScenario, Instrument, NoteRecordPackage
from notes.tools import generate_notes, compile_notes_per_skilllevel, generate_progress_from_str_notes


@login_required
def notes_home(request):
    if request.htmx:
        action = request.POST.get('action')
        if action == 'delete':
            learningscenario_id = request.POST.get('id')
            LearningScenario.objects.get(id=learningscenario_id).delete()
        else:
            raise Exception("unknown action")
        return HttpResponse('', status=200)
    context = {
        'learningscenarios': LearningScenario.objects.filter(user=request.user).order_by('-created'),
    }
    return render(request, 'notes/learn.html', context=context)


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
            instrument = form.cleaned_data['instrument']
            transposing_direction = instrument_infos[instrument].get('transposing_direction', 0)
            ls.transposing_direction = transposing_direction
            ls.save()
            return redirect(reverse('notes-home'))

    if not form:
        form = LearningScenarioForm(instance=model)

    context = {'form': form,
               'learningscenario_pk': model.pk,
               'instruments_info': instrument_infos,
               'new': request.GET.get('new', False),}

    return render(request, 'notes/learningscenario_edit.html', context=context)


def edit_learningscenario_notes(request, pk: int):
    ls: LearningScenario = LearningScenario.objects.get(id=pk)

    # not sure why request.POST does not suffice. Perhaps cos JSON sent
    if request.method == 'POST':
        received = json.loads(request.body)
        notes_added = received['added']
        notes_removed = received['removed']
        ls.edit_notes(added=notes_added, removed=notes_removed)
        return JsonResponse({'success': True}, status=200)

    lowest_note, highest_note = Instrument.get_instrument_range(ls.instrument.name)

    all_notes = [str(note) for note in generate_notes(lowest_note=lowest_note, highest_note=highest_note)]

    context = {'notes': ls.simple_vocab(), 'all_notes': all_notes}

    return render(request, 'notes/learningscenario_edit_vocab.html', context=context)


def common_context(instrument: Instrument, sound:bool):
    instrument_info = instrument_infos[instrument.name.lower()]
    if sound:
        instrument_template = 'notes/instruments/mic_input.html'
        score_css = 'justify-content-center'
    else:
        instrument_template = 'notes/instruments/' + instrument_info['answer_template']
        score_css = ''

    return {'answers_json': instrument_info['answers'],
            'instrument_template': instrument_template,
            'clef': instrument.clef.lower(),
            'instrument': instrument.name,
            'score_css': score_css,
            }


def practice(request, learningscenario_id: int, sound:bool=False):
    package, serialised_notes = LearningScenario.progress_latest_serialised(learningscenario_id)
    instrument_instance: Instrument = package.instrument()
    learningscenario = LearningScenario.objects.get(id=learningscenario_id)
    context = {
        'learningscenario_id': learningscenario_id,
        'package_id': package.id,
        'key': learningscenario.key,
        'transosing_direction': learningscenario.transposing_direction,
        'progress': serialised_notes,
        'sound': sound,
    }
    context.update(common_context(instrument_instance, sound))

    return render(request, 'notes/practice.html', context=context)


def practice_try(request, instrument: str, clef:str, level: str, sound:bool=False):
    instrument_instance = Instrument.objects.get(name=instrument, level=level, clef=clef.upper())
    serialised_notes = generate_progress_from_str_notes(instrument_instance.notes_str)

    instrument_info = instrument_infos[instrument.lower()]
    keys = instrument_info.get('common_keys')

    context = {
        'progress': serialised_notes,
        'instrument_id': instrument_instance.id,
        'key': keys[0],
        'transosing_direction': instrument_info.get('transposing_direction', 0),
        'level': level,
        'sound': sound,
    }

    context.update(common_context(instrument_instance, sound))

    rt_per_sl = compile_notes_per_skilllevel([{'note': n['note'], 'alter': n['alter'], 'octave': n['octave']}
                                              for n in serialised_notes])
    graph_context = {
        'progress': serialised_notes,
        'rt_per_sk': rt_per_sl,
    }
    context.update(graph_context)

    return render(request, 'notes/practice_try.html', context=context)


def practice_data(request, package_id: int):
    learningscenario: NoteRecordPackage = NoteRecordPackage.objects.get(id=package_id)

    json_data = json.loads(request.body)
    learningscenario.process_answers(json_data)

    return JsonResponse({'success': True})


def instrument_data(request, instrument):
    return None


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

def learningscenario_graph_try(request, instrument: str, clef: str, level: str):

    if request.method == 'POST':
        serialised_notes = json.loads(request.body)
    else:
        instrument_instance = Instrument.objects.get(name=instrument, clef=clef.upper(), level=level)
        serialised_notes = generate_progress_from_str_notes(instrument_instance.notes_str)

    rt_per_sl = compile_notes_per_skilllevel([{'note': n['note'], 'alter': n['alter'], 'octave': n['octave']}
                                              for n in serialised_notes])

    context = {
        #'learningscenario_id': learningscenario_id,
        # 'package_id': package.id,
        'package': None,
        'progress': serialised_notes,
        'rt_per_sk': rt_per_sl,
    }

    return render(request, 'notes/learningscenario_graph_try.html', context=context)

