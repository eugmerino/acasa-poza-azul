from django.shortcuts import render
from .models import Fee, Range

def fee_list(request):
    fees = Fee.objects.all()
    return render(request, 'tarifas.html', {'fees': fees})
