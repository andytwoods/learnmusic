from django.contrib import admin
from django.utils.text import Truncator

from .models import LearningScenario, NoteRecordPackage



@admin.register(NoteRecordPackage)
class NoteRecordPackageAdmin(admin.ModelAdmin):
    # note that user and instrument are functions within NoteRecordPackage
    list_display = ('modified', 'short_log', 'user', 'learningscenario',)  # Key fields for overview
    search_fields = ('learningscenario__user__username',)  # Search for users/scenarios

    def short_log(self, obj):
        return Truncator(obj.log).chars(40)  # Truncate to 40 characters

    short_log.short_description = 'Log'  # Display name for the truncated log in the admin

# Custom Admin for LearningScenario
@admin.register(LearningScenario)
class LearningScenarioAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'clef', 'last_practiced')  # Key fields for Learning Scenarios
    list_filter = ('clef', )  # Filters for related fields
    readonly_fields = ('last_practiced', 'days_old')  # Read-only computed fields
