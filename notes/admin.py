from django.contrib import admin
from .models import Note, Instrument, LearningScenario, NoteRecord, NoteRecordPackage


# Custom Admin for Note
@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'note', 'alter', 'octave')  # Display fields in the admin list
    list_filter = ('note', 'alter', 'octave')  # Add filters for relevant fields
    search_fields = ('note', 'octave')  # Searchable by note and octave
    ordering = ('note', 'octave')  # Default ordering


# Custom Admin for Instrument
@admin.register(Instrument)
class InstrumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'level', 'clef', 'lowest_note', 'highest_note')  # Key fields to display
    list_filter = ('level', 'clef')  # Filters for level and clef
    search_fields = ('name',)  # Searchable by instrument name
    ordering = ('name', 'level')  # Sorting by name and level
    readonly_fields = ('lowest_note', 'highest_note')  # Prevent accidental edits


@admin.register(NoteRecordPackage)
class NoteRecordPackageAdmin(admin.ModelAdmin):
    # note that user and instrument are functions within NoteRecordPackage
    list_display = ('id', 'user', 'instrument', 'learningscenario', 'created', "modified")  # Key fields for overview
    list_filter = ('learningscenario', 'created')  # Filters for related fields
    search_fields = ('learningscenario__user__username',)  # Search for users/scenarios


# Inline for Notes in LearningScenario
class VocabularyInline(admin.TabularInline):
    model = LearningScenario.vocabulary.through  # Inline for many-to-many field
    extra = 0
    verbose_name = 'Vocabulary Note'
    verbose_name_plural = 'Vocabulary Notes'


# Custom Admin for LearningScenario
@admin.register(LearningScenario)
class LearningScenarioAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'instrument', 'clef', 'last_practiced')  # Key fields for Learning Scenarios
    list_filter = ('instrument', 'clef')  # Filters for related fields
    search_fields = ('user__username', 'instrument__name')  # Facilitate search by user or instrument
    inlines = [VocabularyInline]  # Inline for vocabulary notes
    readonly_fields = ('last_practiced', 'days_old')  # Read-only computed fields


# Custom Admin for NoteRecord
@admin.register(NoteRecord)
class NoteRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'note', 'learningscenario', 'reaction_time', 'n')  # Key fields to show
    list_filter = ('learningscenario',)  # Filter by learning scenario
    search_fields = ('note__note', 'learningscenario__user__username')  # Search by note or user
    ordering = ('-reaction_time',)  # Order by reaction time (descending)
