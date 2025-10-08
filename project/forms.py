from django import forms
from .models import Project, Community, Directive, Partner
from django.urls import reverse
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
        if not re.match(r'^[A-Za-z0-9ñÑ ]+$', name):
            raise forms.ValidationError("El nombre solo puede contener letras, números y espacios.")

        # Validar unicidad ignorando mayúsculas/minúsculas
        qs = Community.objects.filter(name__iexact=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Ya existe una comunidad con este nombre.")

        return name

class DirectiveForm(forms.ModelForm):
    partner_search = forms.CharField(
        label='Buscar Directivo (por nombre o DUI)',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Escribe para buscar...',
        })
    )

    class Meta:
        model = Directive
        fields = ['role', 'partner']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'}),
            'partner': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        roles_choices = [(choice.value, choice.label) for choice in Directive.Roles]
        self.fields['role'].choices = [('', 'Seleccione un cargo...')] + roles_choices

