from django import forms
from .models import Project, Community, Partner
import re
from django.core.exceptions import ValidationError

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


class PartnerForm(forms.ModelForm):
    class Meta:
        model = Partner
        fields = ["first_name", "last_name", "foto", "dui", "tel", "email", "community"]
        labels = {
            "community": "Comunidad",
        }
        widgets = {
            "first_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ingrese los nombres del socio"
            }),
            "last_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ingrese los apellidos del socio"
            }),
            "foto": forms.FileInput(attrs={
                "id": "id_foto",
                "class": "form-control"
            }),
            "dui": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ingrese el DUI del socio"
            }),
            "tel": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ingrese el teléfono del socio"
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "Ingrese el correo electrónico del socio"
            }),
            "community": forms.Select(attrs={
                "class": "form-select",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["community"].empty_label = "Seleccione una comunidad..."

    # --- VALIDACIONES ---

    def clean_first_name(self):
        first_name = self.cleaned_data.get("first_name", "").strip()
        if not first_name:
            raise forms.ValidationError("El nombre es obligatorio.")
        if re.search(r"[^A-Za-zÁÉÍÓÚáéíóúÑñ\s]", first_name):
            raise forms.ValidationError("El nombre solo puede contener letras y espacios.")
        if "  " in first_name:
            raise forms.ValidationError("El nombre no puede contener dos espacios seguidos.")
        if first_name.startswith(" "):
            raise forms.ValidationError("El nombre no puede comenzar con espacio.")
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get("last_name", "").strip()
        if not last_name:
            raise forms.ValidationError("El apellido es obligatorio.")
        if re.search(r"[^A-Za-zÁÉÍÓÚáéíóúÑñ\s]", last_name):
            raise forms.ValidationError("El apellido solo puede contener letras y espacios.")
        if "  " in last_name:
            raise forms.ValidationError("El apellido no puede contener dos espacios seguidos.")
        if last_name.startswith(" "):
            raise forms.ValidationError("El apellido no puede comenzar con espacio.")
        return last_name

    def clean_dui(self):
        dui = (self.cleaned_data.get("dui") or "").strip()
        if not dui:
            raise forms.ValidationError("El DUI es obligatorio.")
        if not re.fullmatch(r"\d{8}-\d", dui):
            raise forms.ValidationError("El formato del DUI debe ser ########-#")
        return dui

    def clean_tel(self):
        tel = (self.cleaned_data.get("tel") or "").strip()
        if not tel:
            raise forms.ValidationError("El teléfono es obligatorio.")
        if not re.fullmatch(r"\d{4}-\d{4}", tel):
            raise forms.ValidationError("El formato del teléfono debe ser ####-####")
        return tel

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip()
        if email:
            pattern = r"^[\w\.-]+@gmail\.com$"
            if not re.fullmatch(pattern, email, re.IGNORECASE):
                raise forms.ValidationError("El correo debe tener formato válido y ser @gmail.com")
        return email

    def clean_community(self):
        community = self.cleaned_data.get("community")
        if not community:
            raise forms.ValidationError("Debe seleccionar una comunidad.")
        return community