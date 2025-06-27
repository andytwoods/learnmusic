from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, Submit, HTML
from django.forms import DateTimeInput
from django.utils import timezone
from datetime import datetime
from zoneinfo import ZoneInfo

from .instruments import instrument_infos
from .models import LearningScenario


class LearningScenarioForm(forms.ModelForm):

    class Meta:
        model = LearningScenario
        fields = ['instrument_name', 'label', 'level', 'clef', 'key', 'transpose_key', 'reminder', 'reminder_type']


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
        if self.instance and self.instance.reminder and self.request and hasattr(self.request.user, 'profile'):
            user_timezone = self.request.user.profile.timezone
            if timezone.is_aware(self.instance.reminder):
                # Convert from UTC to user's timezone
                local_reminder = self.instance.reminder.astimezone(ZoneInfo(user_timezone))
                self.initial['reminder'] = local_reminder

        self.fields['reminder'] = forms.DateTimeField(
            widget=DateTimeInput(
                attrs={
                    "type": "datetime-local",     # HTML5 widget
                    "class": "form-control",      # bootstrap styling, optional
                }
            ),
            input_formats=["%Y-%m-%dT%H:%M"],      # matches datetime-local
            required=False,                       # or True if the field is mandatory
            label="Daily reminder time",
            help_text="Set in your local timezone"
        )

        # Crispy Forms for layout
        self.helper = FormHelper()
        self.helper.form_method = 'post'

        # Modify layout to include the new field
        self.helper.layout = Layout(
            Field('instrument_name'),
            Field('label'),
            Field('level'),
            Field('reminder_type'),
            Field('reminder'),
            HTML('<div class="mb-3"><button type="button" class="btn btn-secondary" data-bs-toggle="collapse" '
                 'data-bs-target="#advanced-collapse" aria-expanded="false" aria-controls="advanced-collapse">'
                 'Advanced Options</button></div>'),
            Div(
                Field('clef'),
                Field('key'),
                Field('transpose_key'),
                css_id='advanced-collapse',  # This div controls showing/hiding advanced fields
                css_class='collapse'  # Hidden by default via Bootstrap's `.collapse`
            ),
            Submit('submit', 'Submit')
        )

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Convert reminder from user's timezone to UTC if it exists
        if self.cleaned_data.get('reminder') and self.request and hasattr(self.request.user, 'profile'):
            reminder = self.cleaned_data.get('reminder')
            user_timezone = self.request.user.profile.timezone

            # If the reminder is naive (no timezone info), make it aware using user's timezone
            if timezone.is_naive(reminder):
                aware_reminder = timezone.make_aware(reminder, ZoneInfo(user_timezone))
                # Convert to UTC for storage
                utc_reminder = aware_reminder.astimezone(timezone.utc)
                instance.reminder = utc_reminder

        if commit:
            instance.save()

        return instance
