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

from .instruments import instrument_infos
from .models import LearningScenario


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
        fields = ['instrument_name', 'label', 'level', 'clef', 'key', 'transpose_key', 'octave_shift', 'reminder',
                  'reminder_type']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(LearningScenarioForm, self).__init__(*args, **kwargs)

        self.fields['transpose_key'].label = 'Transposing to which key'

        self.fields['instrument_name'] = forms.ChoiceField(
            choices=[(i, i) for i in instrument_infos.keys()],
            widget=forms.Select,
            label="Instrument Name"
        )

        # Convert reminder from UTC to user's timezone if it exists
        if self.instance and self.instance.reminder and self.request:
            user_timezone = self.request.user.timezone
            if timezone.is_aware(self.instance.reminder):
                # Convert from UTC to user's timezone
                local_reminder = self.instance.reminder.astimezone(ZoneInfo(user_timezone))
                self.initial['reminder'] = local_reminder

        self.fields['reminder'] = forms.DateTimeField(
            widget=DateTimeInput(
                attrs={
                    "type": "datetime-local",  # HTML5 widget
                    "class": "form-control",  # bootstrap styling, optional
                }
            ),
            input_formats=["%Y-%m-%dT%H:%M"],  # matches datetime-local
            required=False,  # or True if the field is mandatory
            label="Daily reminder time",
            help_text="Set in your local timezone. Specify the next time you want to be reminded. "
                      "Thereafter, you will be reminded at the same time every 24 hours."
        )

        # Crispy Forms for layout
        self.helper = FormHelper()
        self.helper.form_method = 'post'

        # Modify layout to include the new field
        self.helper.layout = Layout(
            Field('instrument_name'),
            Field('label'),
            Field('level'),
            HTML('<div class="mb-3"><button type="button" class="btn btn-secondary" data-bs-toggle="collapse" '
                 'data-bs-target="#advanced-collapse" aria-expanded="false" aria-controls="advanced-collapse">'
                 'Advanced Options</button></div>'),
            Div(
                Div(
                    HTML('<div class="card-header bg-secondary text-white">Advanced Options</div>'),
                    Div(
                        Field('clef'),
                        Field('key'),
                        Field('octave_shift'),
                        Field('transpose_key'),
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

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Convert reminder from user's timezone to UTC if it exists
        if self.cleaned_data.get('reminder') and self.request:
            reminder = self.cleaned_data.get('reminder')

            user_timezone = self.request.user.timezone

            # If the reminder is naive (no timezone info), make it aware using user's timezone
            if timezone.is_naive(reminder):
                aware_reminder = timezone.make_aware(reminder, ZoneInfo(user_timezone))
                # Convert to UTC for storage
                utc_reminder = aware_reminder.astimezone(timezone.utc)
                instance.reminder = utc_reminder

        if commit:
            instance.save()

        return instance
