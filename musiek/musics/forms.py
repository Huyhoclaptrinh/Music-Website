from django import forms
from .models import Music

class DateForm(forms.Form):
    date = forms.DateTimeField(
        input_formats=['%Y-%m-%d'],
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control datetimepicker-input',
            'data-target': '#datetimepicker1',
            'data-date-format': 'YYYY-MM-DD',
        })
    )

class AddSongForm(forms.Form):
    selected_songs = forms.ModelMultipleChoiceField(queryset=Music.objects.all(), widget=forms.CheckboxSelectMultiple)
