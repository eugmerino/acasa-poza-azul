from django import forms
from .models import Project, Community
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


class CommunityForm(forms.ModelForm):
    class Meta:
        model = Community
        fields = ["project", "name", "description"]
        widgets = {
            "project": forms.Select(attrs={
                "class": "form-select"
            }),
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ingrese el nombre de la comunidad"
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Ingrese una breve descripción"
            }),
        }

    # 🔹 Validaciones personalizadas
    def clean_name(self):
        name = self.cleaned_data.get("name")

        # Validar longitud mínima
        if len(name) < 3:
            raise forms.ValidationError("El nombre debe tener al menos 3 caracteres.")

        # Validar que solo contenga letras, números y espacios
        if not re.match(r'^[A-Za-z0-9 ]+$', name):
            raise forms.ValidationError("El nombre solo puede contener letras, números y espacios.")

        # Validar unicidad ignorando mayúsculas/minúsculas
        qs = Community.objects.filter(name__iexact=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Ya existe una comunidad con este nombre.")

        return name
