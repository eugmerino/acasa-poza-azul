from django import forms
from .models import Project, Community, Directive, Partner, WaterConnection
from django.urls import reverse
from django.contrib.auth.models import Group
import re
from django.core.exceptions import ValidationError
from django.utils import timezone

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
    

class UsersForm(forms.ModelForm):
    groups = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=True,  # <- obligatorio
        label="Rol de usuario",
        widget=forms.Select(attrs={"class": "form-select"})
    )
    email = forms.CharField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "Ingrese el correo electrónico"
        })
    )

    class Meta:
        model = Partner
        fields = ["email", "groups", "is_staff"]
        labels = {
            "email": "Correo electrónico",
            "is_staff": "Usuario staff",
        }
        widgets = {
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "Ingrese el correo electrónico"}),
            "is_staff": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip()
        if not email:
            raise forms.ValidationError("El correo es obligatorio.")
        pattern = r"^[\w\.-]+@gmail\.com$"
        if not re.fullmatch(pattern, email, re.IGNORECASE):
            raise forms.ValidationError("El correo debe tener formato válido y ser @gmail.com")
        return email

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["groups"].empty_label = "Seleccione un rol..."

        # Solo asignar initial si no hay datos POST
        if self.instance.pk and not self.data:
            first_group = self.instance.groups.first()
            if first_group:
                self.fields["groups"].initial = first_group.pk

        # Agregar clase 'is-invalid' automáticamente a los campos con error
        for field_name, field in self.fields.items():
            if self.errors.get(field_name):
                css_class = field.widget.attrs.get("class", "")
                field.widget.attrs["class"] = f"{css_class} is-invalid"


    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            # Reasigna el grupo único seleccionado
            group = self.cleaned_data.get("groups")
            user.groups.clear()
            if group:
                user.groups.add(group)
        return user
    

class ConnectionForm(forms.Form):
    class Meta:
        model = WaterConnection
        fields = ["owner", "responsible", "date", "description", "acquisition_price"]
        labels = {
            "owner": "Propietario",
            "responsible": "Responsable",
            "date": "Fecha de adquisición",
            "description": "Descripción",
            "acquisition_price": "Precio de adquisición",
        }

        help_texts = {
            "description": "Descripción corta de la acometida",
        }
        widgets = {
            "owner": forms.Select(
                attrs={
                    "class": "form-select",
                    "required": True,
                }
            ),
            "responsible": forms.Select(
                attrs={
                    "class": "form-select",
                    "required": False,
                }
            ),
            "date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                    "value": timezone.localtime().date(),
                }
            ),
            "description": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ej. Conexión principal casa #4",
                    "maxlength": 200,
                    "required": True,
                }
            ),
            "acquisition_price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "0.00",
                    "step": "0.01",
                    "min": "0",
                    "required": True,
                }
            ),
        }