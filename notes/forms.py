from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, Submit
from .models import LearningScenario


class LearningScenarioForm(forms.ModelForm):

    class Meta:
        model = LearningScenario
        fields = ['instrument', 'clef', 'key']
        labels = {
            'instrument': 'Instrument',
            'clef': 'Clef',
            'key': 'Instrument Key'
        }

    def __init__(self, *args, **kwargs):
        super(LearningScenarioForm, self).__init__(*args, **kwargs)

        # Crispy Forms for layout
        self.helper = FormHelper()
        self.helper.form_method = 'post'

        # Modify layout to include the new field
        self.helper.layout = Layout(
            Field('instrument'),
            Div(
                Field('clef'),
                Field('key'),
                css_id='advanced-collapse',  # This div controls showing/hiding advanced fields
                css_class='collapse'  # Hidden by default via Bootstrap's `.collapse`
            ),
            Submit('submit', 'Submit')
        )
