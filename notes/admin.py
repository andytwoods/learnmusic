from django.contrib import admin
from .models import Instrument, LearningScenario, NoteRecordPackage



# Custom Admin for Instrument
@admin.register(Instrument)
class InstrumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'level', 'clef', 'lowest_note', 'highest_note', 'notes', )  # Key fields to display
    list_filter = ('level', 'clef')  # Filters for level and clef
    search_fields = ('name',)  # Searchable by instrument name
    ordering = ('name', 'level')  # Sorting by name and level
    readonly_fields = ('lowest_note', 'highest_note')  # Prevent accidental edits


@admin.register(NoteRecordPackage)
class NoteRecordPackageAdmin(admin.ModelAdmin):
    # note that user and instrument are functions within NoteRecordPackage
    list_display = ('id', 'log', 'user', 'instrument', 'learningscenario', 'created', "modified")  # Key fields for overview
    list_filter = ('learningscenario', 'created')  # Filters for related fields
    search_fields = ('learningscenario__user__username',)  # Search for users/scenarios



# Custom Admin for LearningScenario
@admin.register(LearningScenario)
class LearningScenarioAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'instrument', 'clef', 'last_practiced')  # Key fields for Learning Scenarios
    list_filter = ('instrument', 'clef')  # Filters for related fields
    search_fields = ('user__username', 'instrument__name')  # Facilitate search by user or instrument
    readonly_fields = ('last_practiced', 'days_old')  # Read-only computed fields
