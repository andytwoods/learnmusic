from django.contrib import admin
from .models import LearningScenario, NoteRecordPackage



@admin.register(NoteRecordPackage)
class NoteRecordPackageAdmin(admin.ModelAdmin):
    # note that user and instrument are functions within NoteRecordPackage
    list_display = ('id', 'log', 'user', 'learningscenario', 'created', "modified")  # Key fields for overview
    list_filter = ('learningscenario', 'created')  # Filters for related fields
    search_fields = ('learningscenario__user__username',)  # Search for users/scenarios



# Custom Admin for LearningScenario
@admin.register(LearningScenario)
class LearningScenarioAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'clef', 'last_practiced')  # Key fields for Learning Scenarios
    list_filter = ('clef', )  # Filters for related fields
    readonly_fields = ('last_practiced', 'days_old')  # Read-only computed fields
