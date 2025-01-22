from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, Submit

from .instruments import instrument_infos
from .models import LearningScenario


class LearningScenarioForm(forms.ModelForm):

    class Meta:
        model = LearningScenario
        fields = ['instrument_name', 'level', 'clef', 'key']
        labels = {
            'instrument_name': 'Instrument',
            'clef': 'Clef',
            'level': 'Level',
            'key': 'Instrument Key'
        }

    def __init__(self, *args, **kwargs):
        super(LearningScenarioForm, self).__init__(*args, **kwargs)

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
            Div(
                Field('clef'),
                Field('level'),
                Field('key'),
                css_id='advanced-collapse',  # This div controls showing/hiding advanced fields
                css_class='collapse'  # Hidden by default via Bootstrap's `.collapse`
            ),
            Submit('submit', 'Submit')
        )
