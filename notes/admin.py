from django import forms
from django.contrib import admin
from django.utils.text import Truncator

from .models import LearningScenario, NoteRecordPackage, validate_signatures_array


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
    list_display = ('id', 'user', 'clef', 'last_practiced', 'preview_signatures')  # Key fields for Learning Scenarios
    list_filter = ('clef', )  # Filters for related fields
    readonly_fields = ('last_practiced', 'days_old')  # Read-only computed fields

    def preview_signatures(self, obj):
        # e.g. “0, 1♯, 2♭  →  C, G, Bb”
        def fmt(n):
            if n == 0: return "0"
            sym = "♯" if n > 0 else "♭"
            return f"{abs(n)}{sym}"

        nums = ", ".join(fmt(n) for n in obj.signatures_sorted)
        keys = ", ".join(obj.vexflow_keys)
        return f"{nums}  →  {keys}"


class LearningScenarioForm(forms.ModelForm):
    # Replace free-form JSON editing with a friendlier MultiValue field of ints
    signatures = forms.JSONField(
        required=False,
        help_text="List integers in [-7..7], e.g. [0, 1, -2]",
        validators=[validate_signatures_array],
    )

    class Meta:
        model = LearningScenario
        fields = "__all__"

    def clean_signatures(self):
        data = self.cleaned_data.get("signatures") or []
        # normalise order for nicer diffs
        data = sorted(set(int(v) for v in data))
        validate_signatures_array(data)
        return data
