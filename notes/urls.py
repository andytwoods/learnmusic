# ruff: noqa
from django.contrib.auth.decorators import login_required
from django.urls import path

from notes import views

urlpatterns = [
    path("practice/", views.notes_home, name="notes-home"),
    path("new-learning-scenario/", views.new_learningscenario, name='new-learning-scenario'),
    path("edit-learning-scenario/<int:pk>/",views.edit_learningscenario, name='edit-learning-scenario'),
    path("edit-learning-scenario-notes/<int:pk>/", views.edit_learningscenario_notes,
         name='edit-learning-scenario-notes'),

    path("practice/<int:learningscenario_id>/",views.practice, name='practice'),

    path('practice/<str:instrument>/<str:level>/', views.practice_try, name='practice-try'),

    path("practice-data/<int:package_id>/", views.practice_data, name='practice-data'),

    path("practice/graph/<int:learningscenario_id>/", views.learningscenario_graph, name='learningscenario_graph'),
]
