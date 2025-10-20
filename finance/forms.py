# finance/forms.py
from django import forms
from .models import Transaction

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['project', 'concept', 'type', 'amount']  # <--- NO incluir 'date'
        widgets = {
            'project': forms.Select(attrs={'class': 'form-select'}),
            'concept': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Concepto de la transacción'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }
        labels = {
            'project': 'Proyecto',
            'concept': 'Concepto',
            'type': 'Tipo',
            'amount': 'Monto',
        }

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is None or amount <= 0:
            raise forms.ValidationError("El monto debe ser mayor a 0.")
        return amount
