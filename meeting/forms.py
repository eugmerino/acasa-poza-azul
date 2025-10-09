from django import forms
from .models import Meeting, Attendance
from datetime import date

class MeetingForm(forms.ModelForm):
    class Meta:
        model = Meeting
        fields = ["title", "date", "start_time", "end_time", "isActive"]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ingrese el título de la reunión"
            }),
            "date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),
            "start_time": forms.TimeInput(attrs={
                "class": "form-control",
                "type": "time"
            }),
            "end_time": forms.TimeInput(attrs={
                "class": "form-control",
                "type": "time"
            }),
            "isActive": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
        }

    def clean_date(self):
        meeting_date = self.cleaned_data.get("date")
        if meeting_date and meeting_date <= date.today():
            raise forms.ValidationError("La fecha debe ser mayor a hoy.")
        return meeting_date

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")
        meeting_date = cleaned_data.get("date")

        if start_time and end_time and start_time >= end_time:
            self.add_error("end_time", "La hora de fin debe ser mayor que la hora de inicio.")

        if meeting_date:
            qs = Meeting.objects.filter(date=meeting_date)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                self.add_error("date", "Ya existe una reunión programada en esta fecha.")

        return cleaned_data

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        # Ahora solo elegimos el socio, la reunión se asigna automáticamente
        fields = ["partner"]

        widgets = {
            "partner": forms.Select(attrs={
                "class": "form-select",
                "placeholder": "Seleccione socio"
            }),
        }
