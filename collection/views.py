from django.shortcuts import render
from .models import Fee
from django.http import JsonResponse

def fee_list(request):
    fees = Fee.objects.all()
    return render(request, 'tarifas.html', {'fees': fees})

def fees_json(request):
    fees = Fee.objects.all()
    data = [
        {
            'id': fee.id,
            'short_description': fee.short_description,
            'approval_date': fee.approval_date.strftime('%d-%m-%Y'),
            'isActive': "Activa" if fee.isActive else "Inactiva",
        }
        for fee in fees
    ]
    return JsonResponse({'data': data})