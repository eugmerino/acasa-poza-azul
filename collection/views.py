from django.shortcuts import render, get_object_or_404, redirect
from .models import Fee
from project.models import Project
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
from datetime import datetime
from django.utils import timezone



def fee_list(request):
    project = Project.objects.first()
    per_page_options = [5, 10, 20, 50]

    query = request.GET.get('q', '') 
    page_number = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', per_page_options[1]))

    fee_list = Fee.objects.all().order_by('-isActive')
    paginator = Paginator(fee_list, per_page)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'fee/tarifas.html',
        {
            'fee_search_url': reverse('fee_search'),
            'page_obj': page_obj,
            'query': query,
            'per_page': per_page,
            'per_page_options': per_page_options,
            'project': project,
        }
    )


def fee_search(request):
    per_page_options = [5, 10, 20, 50]

    query = request.GET.get('q', '').strip()
    page_number = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', per_page_options[1]))

    filters = Q(short_description__icontains=query) | Q(approval_date__icontains=query)

    # Buscar por estado (activa / inactiva)
    if query.lower() in ["activa", "activo", "true", "sí", "si"]:
        filters |= Q(isActive=True)
    elif query.lower() in ["inactiva", "inactivo", "false", "no"]:
        filters |= Q(isActive=False)

    fee_list = Fee.objects.filter(filters).order_by('-isActive')

    paginator = Paginator(fee_list, per_page)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'partials/fee/fee_table.html',
        {
            'fee_search_url': reverse('fee_search'),
            'page_obj': page_obj,
            'query': query,
            'per_page': per_page,
            'per_page_options': per_page_options,
        }
    )

def fee_create_form(request):
    project = Project.objects.first()
    contexto = {
        'hoy': localtime(),
        'project': project,
    }
    return render(request, 'fee/crud_tarifas.html', contexto)    

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
    return render(request, "fee/ver_tarifa.html", contexto)

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


def fee_activate(request, pk):
    fee = get_object_or_404(Fee, pk=pk)
    fee.isActive = True
    fee.save()
    return redirect("fee_list")


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