from django.shortcuts import render, get_object_or_404
from .models import Fee
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from .models import Fee, Range
from django.utils.timezone import localtime
from django.core.serializers.json import DjangoJSONEncoder
from django.core.paginator import Paginator
from django.urls import reverse
from django.db.models import Q


def fee_list(request):
    per_page_options = [5, 10, 20, 50]

    query = request.GET.get('q', '') 
    page_number = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', per_page_options[1]))

    fee_list = Fee.objects.all().order_by('-isActive')
    paginator = Paginator(fee_list, per_page)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'tarifas.html',
        {
            'fee_search_url': reverse('fee_search'),
            'page_obj': page_obj,
            'query': query,
            'per_page': per_page,
            'per_page_options': per_page_options,
        }
    )


def fee_search(request):
    per_page_options = [5, 10, 20, 50]

    query = request.GET.get('q', '') 
    page_number = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', per_page_options[1]))

    fee_list = Fee.objects.filter(
        Q(short_description__icontains=query)
    ).order_by('-isActive')

    paginator = Paginator(fee_list, per_page)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'partials/fee_table.html',
        {
            'fee_search_url': reverse('fee_search'),
            'page_obj': page_obj,
            'query': query,
            'per_page': per_page,
            'per_page_options': per_page_options,
        }
    )

def fee_create_form(request):
    contexto = {
        'hoy': localtime()
    }
    return render(request, 'crud_tarifas.html', contexto)    

def ver_tarifa(request, tarifa_id):
    tarifa = get_object_or_404(Fee, pk=tarifa_id)
    tramos = tarifa.Fee_ranges.all().order_by('min_meter')

    # Convertir tramos a JSON seguro
    tramos_json = json.dumps([
        {
            "min_meter": t.min_meter,
            "max_meter": t.max_meter if t.max_meter is not None else None,
            "fixed_amount": float(t.fixed_amount),
            "amount_meter": float(t.amount_meter or 0)
        }
        for t in tramos
    ], cls=DjangoJSONEncoder)

    contexto = {
        "tarifa": tarifa,
        "tramos": tramos,
        "tramos_json": tramos_json,
        "hoy": localtime()
    }
    return render(request, "ver_tarifa.html", contexto)

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

@csrf_exempt
@require_POST
def fee_activate(request):
    fee_id = request.POST.get('id')
    try:
        fee = Fee.objects.get(pk=fee_id)
        fee.isActive = True
        fee.save()
        return JsonResponse({'success': True})
    except Fee.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Tarifa no encontrada'})

@csrf_exempt
@require_POST
def fee_create(request):
    try:
        data = json.loads(request.body)
        descripcion = data.get('descripcion')
        fecha_aprobacion = data.get('fecha_aprobacion')
        activa = data.get('activa', False)
        tramos = data.get('tramos', [])

        fee = Fee.objects.create(
            short_description=descripcion,
            approval_date=fecha_aprobacion,
            isActive=activa
        )

        for tramo in tramos:
            Range.objects.create(
                fee=fee,
                min_meter=tramo['metro_inicial'],
                max_meter=None if tramo['metro_final'] == '-' else tramo['metro_final'],
                fixed_amount=tramo['monto_fijo'],
                amount_meter=tramo['monto_adicional'] or 0
            )

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})