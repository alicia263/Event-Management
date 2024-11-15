# forms.py
from django import forms
from .models import Event

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = '__all__'
        exclude = ['created_by']



class EventSelectionForm(forms.Form):
    event = forms.ModelChoiceField(queryset=Event.objects.all(), empty_label="Select an event")