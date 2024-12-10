# admin.py

from django.contrib import admin
from .models import NoteRecord, LearningScenario, Instrument, Note

# Register models
admin.site.register(NoteRecord)
admin.site.register(LearningScenario)
admin.site.register(Instrument)
admin.site.register(Note)
