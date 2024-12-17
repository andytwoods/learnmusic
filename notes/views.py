import json
from wsgiref.util import request_uri

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import UpdateView

from notes import tools
from notes.forms import LearningScenarioForm
from notes.models import LearningScenario

@login_required
def notes_home(request):

    context = {
        'learningscenarios': LearningScenario.objects.filter(user=request.user)
    }
    return render(request, 'notes/learn.html', context=context)


@login_required
def new_learning_scenario(request):
    scenario = LearningScenario(user=request.user)
    scenario.save()
    return redirect(reverse('edit-learning-scenario', kwargs={'pk': scenario.id}))


@login_required
def edit_learning_scenario(request, pk: int):
    model = LearningScenario.objects.get(id=pk)
    form = None
    if request.POST:
        form = LearningScenarioForm(request.POST, instance=model)
        if form.is_valid():
            learningscenario:LearningScenario = form.save(commit=False)
            learningscenario.add_notes_if_none()
            learningscenario.save()
            return redirect(reverse('notes-home'))

    if not form:
        form = LearningScenarioForm(instance=model)

    context = {'form': form,}

    return render(request, 'notes/learning_scenario_edit.html', context=context)


def practice(request, learningscenario_id:int):
    learningscenario: LearningScenario = LearningScenario.objects.get(id=learningscenario_id)
    context = {
        'learningscenario_id': learningscenario_id
    }
    return render(request, 'notes/practice.html', context=context)

def practice_data(request, learningscenario_id:int):
    json_data = json.loads(request.body)
    tools.process_answers(json_data.get('data'))
    return JsonResponse({'success': True})
