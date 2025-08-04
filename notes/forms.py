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

        if commit:
            instance.save()

        return instance
