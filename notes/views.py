import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse

from notes.forms import LearningScenarioForm
from notes.models import LearningScenario, Instrument, NoteRecordPackage
from notes.tools import generate_notes, compile_notes_per_skilllevel


@login_required
def notes_home(request):
    context = {
        'learningscenarios': LearningScenario.objects.filter(user=request.user).order_by('-created'),
    }
    return render(request, 'notes/learn.html', context=context)


@login_required
def new_learningscenario(request):
    scenario = LearningScenario(user=request.user)
    scenario.save()
    return redirect(reverse('edit-learning-scenario', kwargs={'pk': scenario.id}))


@login_required
def edit_learningscenario(request, pk: int):
    model = LearningScenario.objects.get(id=pk)
    form = None
    if request.POST:
        form = LearningScenarioForm(request.POST, instance=model)
        if form.is_valid():
            form.save()
            return redirect(reverse('notes-home'))

    if not form:
        form = LearningScenarioForm(instance=model)

    context = {'form': form,
               'learningscenario_pk': model.pk}

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


def practice(request, learningscenario_id: int):
    package, serialised_notes = LearningScenario.progress_latest_serialised(learningscenario_id)
    context = {
        'learningscenario_id': learningscenario_id,
        'package_id': package.id,
        'progress': serialised_notes,
    }
    return render(request, 'notes/practice.html', context=context)


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
        'package_id': package.id,
        'progress': serialised_notes,
        'rt_per_sk': rt_per_sl,
    }
    print(context)
    return render(request, 'notes/learningscenario_graph.html', context=context)
