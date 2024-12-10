# forms.py
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms

from .models import LearningScenario, Instrument


class LearningScenarioForm(forms.ModelForm):
    instrument = forms.ModelChoiceField(
        queryset=Instrument.objects.all(),
        empty_label="Select an Instrument",
        widget=forms.Select(attrs={'class': 'dropdown'})
    )
    class Meta:
        model = LearningScenario
        fields = ['instrument']

        # Include fields you want in the form

    def __init__(self, *args, **kwargs):
        super(LearningScenarioForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Submit'))
