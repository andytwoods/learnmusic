# ruff: noqa
from django.contrib.auth.decorators import login_required
from django.urls import path
from django.views.generic import TemplateView

from notes import views

urlpatterns = [
    # Test JS URL
    path('test-js/', TemplateView.as_view(template_name='notes/test_js.html'), name='test-js'),

    # Reminder settings HTMX endpoints
    path("reminder-settings-button/", views.reminder_settings_button, name="reminder-settings-button"),
    path("reminder-settings-form/", views.reminder_settings_form, name="reminder-settings-form"),
    path("reminder-settings-submit/", views.reminder_settings_submit, name="reminder-settings-submit"),
    path('progress-data/<int:learningscenario_id>/', views.progress_data_view, name='progress_data'),
    path("progress/<int:learningscenario_id>/", views.progress, name='see-progress'),
    path("practice/", views.notes_home, name="notes-home"),
    path("reminders/", views.reminders, name="reminders"),
    path("new-learning-scenario/", views.new_learningscenario, name='new-learning-scenario'),
    path("edit-learning-scenario/<int:pk>/", views.edit_learningscenario, name='edit-learning-scenario'),
    path("edit-learning-scenario-notes/<int:pk>/", views.edit_learningscenario_notes,
         name='edit-learning-scenario-notes'),

    path("practice/<int:learningscenario_id>/", views.practice, name='practice'),
    path("practice-sound/<int:learningscenario_id>/", views.practice, name='practice-sound', kwargs={'sound': True}),

    path("practice-data/<int:package_id>/", views.practice_data, name='practice-data'),

    path("practice-graph/<int:learningscenario_id>/", views.learningscenario_graph, name='learningscenario_graph'),

    path('practice-demo/', views.practice_demo, name='practice-demo'),
    # Routes without absolute_pitch segment
    path('practice-try/<str:instrument>/<str:clef>/<str:key>/<str:level>/<str:octave>/sigs/<str:signatures>/', views.practice_try, name='practice-try-sigs'),
    path('practice-sound-try/<str:instrument>/<str:clef>/<str:key>/<str:level>/<str:octave>/sigs/<str:signatures>/', views.practice_try,
         kwargs={'sound': True}, name='practice-sound-try-sigs'),
    # Routes including absolute_pitch segment
    path('practice-try/<str:instrument>/<str:clef>/<str:key>/<str:absolute_pitch>/<str:level>/<str:octave>/sigs/<str:signatures>/', views.practice_try, name='practice-try-sigs-abs'),
    # Manifest routes
    path('practice-try/<str:instrument>/<str:clef>/<str:key>/<str:level>/<str:octave>/sigs/<str:signatures>/manifest.json', views.practice_try_manifest, name='practice-try-manifest-sigs'),
    path('practice-try/<str:instrument>/<str:clef>/<str:key>/<str:absolute_pitch>/<str:level>/<str:octave>/sigs/<str:signatures>/manifest.json', views.practice_try_manifest, name='practice-try-manifest-sigs-abs'),
    path('practice-sound-try/<str:instrument>/<str:clef>/<str:key>/<str:absolute_pitch>/<str:level>/<str:octave>/sigs/<str:signatures>/', views.practice_try,
         kwargs={'sound': True}, name='practice-sound-try-sigs'),
    path("learningscenario-graph-try/<str:instrument>/<str:level>/",
         views.learningscenario_graph_try, name='learningscenario_graph_try'),

    path("pushover/callback/", views.pushover_callback, name="pushover_callback"),

    path("cache-to-backend/", views.cache_to_backend, name="cache-to-backend"),


]
