from datetime import timedelta
from zoneinfo import ZoneInfo

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, LayoutObject
from crispy_forms.layout import Layout, Div, Field, Submit, Template
from django import forms
from django.conf import settings
from django.forms import DateTimeInput
from django.template.loader import render_to_string
from django.utils import timezone

from .instrument_data import instrument_infos
from .models import LearningScenario, FIFTHS_TO_VEXFLOW_MAJOR


class CustomTemplate(LayoutObject):
    def __init__(self, template_name, context=None):
        self.template_name = template_name
        self.context = context or {}

    def render(self, form, form_style, context=None, template_pack=None):
        if context:
            self.context.update(self.context)

        return render_to_string(self.template_name, self.context)


class LearningScenarioForm(forms.ModelForm):
    class Meta:
        model = LearningScenario
        fields = ['instrument_name', 'label', 'level', 'clef', 'relative_key', 'absolute_pitch', 'octave_shift', 'reminder',
                  'reminder_type']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(LearningScenarioForm, self).__init__(*args, **kwargs)

        self.fields['absolute_pitch'].label = 'Absolute pitch key'
        self.fields['absolute_pitch'].required = False

        self.fields['instrument_name'] = forms.ChoiceField(
            choices=[(i, i) for i in instrument_infos.keys()],
            widget=forms.Select,
            label="Instrument Name"
        )

        # Convert reminder from UTC to user's timezone if it exists and extract only time
        if self.instance and self.instance.reminder and self.request:
            user_timezone = self.request.user.timezone
            if timezone.is_aware(self.instance.reminder):
                # Convert from UTC to user's timezone
                local_reminder = self.instance.reminder.astimezone(ZoneInfo(user_timezone))
                # Extract only the time component
                self.initial['reminder'] = local_reminder.strftime("%H:%M")

        self.fields['reminder'] = forms.TimeField(
            widget=forms.TimeInput(
                attrs={
                    "type": "time",  # HTML5 time widget
                    "class": "form-control",  # bootstrap styling, optional
                }
            ),
            input_formats=["%H:%M"],  # matches time input format
            required=False,  # or True if the field is mandatory
            label="Daily reminder time",
            help_text="Set the time you want to be reminded daily. The reminder will occur at this time every day."
        )

        # Prepare signatures field and context for the custom template
        # Define a form field to capture multiple signatures (rendered via custom template)
        self.fields['signatures'] = forms.MultipleChoiceField(
            choices=[(str(i), str(i)) for i in range(-7, 8)],
            required=False,
            widget=forms.CheckboxSelectMultiple,
            label="Key signatures"
        )
        # Determine selected signatures from bound data or instance
        if self.is_bound:
            try:
                selected_signatures = [int(x) for x in self.data.getlist('signatures') if x.strip() != ""]
            except Exception:
                selected_signatures = []
        else:
            selected_signatures = list(self.instance.signatures or []) if self.instance else []
        if not selected_signatures:
            selected_signatures = [0]
        # Compose (sig, keyname) pairs for the partial
        signatures_with_names = [(s, FIFTHS_TO_VEXFLOW_MAJOR[s]) for s in range(0, -8, -1)] + \
                                 [(s, FIFTHS_TO_VEXFLOW_MAJOR[s]) for s in range(1, 8)]
        # Set initial for the field (strings for MultipleChoiceField)
        self.fields['signatures'].initial = [str(s) for s in selected_signatures]

        # Crispy Forms for layout
        self.helper = FormHelper()
        self.helper.form_method = 'post'

        # Modify layout to include the new field
        self.helper.layout = Layout(
            Field('instrument_name'),
            Field('label'),
            Field('level'),
            # Insert signatures UI right below 'level'
            CustomTemplate('notes/components/_signatures_form.html', context={
                'signatures_with_names': signatures_with_names,
                'selected_signatures': selected_signatures,
            }),
            HTML('<div class="mb-3"><button type="button" class="btn btn-secondary" data-bs-toggle="collapse" '
                 'data-bs-target="#advanced-collapse" aria-expanded="false" aria-controls="advanced-collapse">'
                 'Advanced Options</button></div>'),
            Div(
                Div(
                    HTML('<div class="card-header bg-secondary text-white">Advanced Options</div>'),
                    Div(
                        Field('clef'),
                        Field('relative_key'),
                        Field('octave_shift'),
                        Field('absolute_pitch'),
                        css_class='card-body bg-light'
                    ),
                    css_class='card shadow-sm'
                ),
                css_id='advanced-collapse',  # This div controls showing/hiding advanced fields
                css_class='collapse mb-3'  # Hidden by default via Bootstrap's `.collapse`
            ),
            Field('reminder_type'),
            Div(
                Div(
                    HTML('<div class="card-header bg-secondary text-white">Reminder Settings</div>'),
                    Div(
                        Field('reminder'),
                        CustomTemplate('crispy/pushover.html',
                                      context={'request': self.request,
                                               'pushover_url': settings.PUSHOVER_SUBSCRIPTION_URL}),
                        css_class='card-body bg-light'
                    ),
                    css_class='card shadow-sm'
                ),
                css_id='reminder_fields',
                css_class='mb-3'
            ),
            Submit('submit', 'Submit')
        )

    def clean_signatures(self):
        raw = self.cleaned_data.get('signatures') or []
        try:
            sigs = [int(x) for x in raw]
        except Exception:
            sigs = []
        # Bound and unique preserve order
        seen = set()
        filtered = []
        for s in sigs:
            if -7 <= s <= 7 and s not in seen:
                seen.add(s)
                filtered.append(s)
        if not filtered:
            filtered = [0]
        return filtered

    def clean_reminder(self):
        """
        Convert the time field value to a datetime object before validation.
        This ensures the model's DateTimeField receives the correct type.

        If the reminder time has already passed for the current day,
        the reminder will be set for the next day.
        """
        time_value = self.cleaned_data.get('reminder')
        if not time_value or not self.request:
            return None

        user_timezone = self.request.user.timezone

        # Get current date and time in user's timezone
        current_datetime = timezone.now().astimezone(ZoneInfo(user_timezone))
        current_date = current_datetime.date()

        # Combine current date with time input
        from datetime import datetime, timedelta
        combined_datetime = datetime.combine(
            current_date,
            time_value
        )

        # Make timezone aware using user's timezone
        aware_reminder = timezone.make_aware(combined_datetime, ZoneInfo(user_timezone))

        # If the reminder time has already passed for today, set it for tomorrow
        if aware_reminder < current_datetime:
            aware_reminder += timedelta(days=1)

        # Convert to UTC for storage
        utc_reminder = aware_reminder.astimezone(ZoneInfo("UTC"))
        return utc_reminder

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Persist signatures from cleaned_data to model instance
        sigs = self.cleaned_data.get('signatures')
        if sigs is not None:
            instance.signatures = sigs

        if commit:
            instance.save()

        return instance
