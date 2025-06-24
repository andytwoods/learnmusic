from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, Submit

from .instruments import instrument_infos
from .models import LearningScenario


class PushNotificationForm(forms.Form):
    """Form for sending push notifications to all users."""
    title = forms.CharField(
        max_length=100,
        required=True,
        initial="Tootology Notification",
        help_text="The title of the push notification."
    )
    message = forms.CharField(
        widget=forms.Textarea,
        required=True,
        help_text="The message body of the push notification."
    )

    def __init__(self, *args, **kwargs):
        super(PushNotificationForm, self).__init__(*args, **kwargs)

        # Crispy Forms for layout
        self.helper = FormHelper()
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('title'),
            Field('message'),
            Submit('submit', 'Send Notification', css_class='btn btn-primary')
        )


class LearningScenarioForm(forms.ModelForm):

    class Meta:
        model = LearningScenario
        fields = ['instrument_name', 'label', 'level', 'clef', 'key', 'transpose_key', ]


    def __init__(self, *args, **kwargs):
        super(LearningScenarioForm, self).__init__(*args, **kwargs)

        self.fields['transpose_key'].label = 'Transposing to which key'

        self.fields['instrument_name'] = forms.ChoiceField(
            choices=[(i, i) for i in instrument_infos.keys()],
            widget=forms.Select,
            label="Instrument Name"
        )

        # Crispy Forms for layout
        self.helper = FormHelper()
        self.helper.form_method = 'post'

        # Modify layout to include the new field
        self.helper.layout = Layout(
            Field('instrument_name'),
            Field('label'),
            Div(
                Field('clef'),
                Field('level'),
                Field('key'),
                css_id='advanced-collapse',  # This div controls showing/hiding advanced fields
                css_class='collapse'  # Hidden by default via Bootstrap's `.collapse`
            ),
            Submit('submit', 'Submit')
        )
