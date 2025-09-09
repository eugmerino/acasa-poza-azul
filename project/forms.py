from django import forms
from .models import Project
import re

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description', 'logo', 'connection_price', 'absence_fine']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'connection_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'absence_fine': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def clean_title(self):
        title = self.cleaned_data.get("title")
        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$', title):
            raise forms.ValidationError(
                "El título solo puede contener letras y espacios."
            )
        return title
