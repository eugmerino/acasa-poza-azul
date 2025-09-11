from django import forms
from .models import Meeting
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

    # 🔹 Validaciones personalizadas
    def clean_title(self):
        title = self.cleaned_data.get("title")
        if len(title) < 5:
            raise forms.ValidationError("El título debe tener al menos 5 caracteres.")
        return title

    def clean_date(self):
        meeting_date = self.cleaned_data.get("date")
        if meeting_date and meeting_date < date.today():
            raise forms.ValidationError("La fecha no puede ser anterior a hoy.")
        return meeting_date

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if start_time and end_time and start_time >= end_time:
            self.add_error("end_time", "La hora de fin debe ser mayor que la hora de inicio.")
        return cleaned_data
