# ruff: noqa
from django.contrib.auth.decorators import login_required
from django.urls import path

from notes import views

urlpatterns = [
    path("", views.notes_home, name="notes-home"),
    path("new-learning-scenario/", views.new_learning_scenario, name='new-learning-scenario'),
    path("edit-learning-scenario/<int:pk>/",views.edit_learning_scenario, name='edit-learning-scenario'),

    path("practice/<int:learningscheme_id>/",views.practice, name='practice')

]
