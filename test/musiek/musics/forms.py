from django import forms

class DateForm(forms.Form):
    date = forms.DateTimeField(
        input_formats=['%Y-%m-%d'],
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control datetimepicker-input',
            'data-target': '#datetimepicker1',
            'data-date-format': 'YYYY-MM-DD',
        })
    )