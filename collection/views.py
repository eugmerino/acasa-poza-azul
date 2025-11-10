from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect, Http404
from .models import Fee, Range, Reading
from project.models import Project, WaterConnection
from meeting.models import Meeting
from .forms import ReadingForm
from django.http import JsonResponse
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from django.utils.timezone import localtime
from django.core.serializers.json import DjangoJSONEncoder
from django.core.paginator import Paginator
from django.urls import reverse
from django.db.models import Exists, Subquery, OuterRef, Q
from django.utils import timezone
from datetime import date
from decimal import Decimal
from django.template.loader import render_to_string
import tempfile
import weasyprint


# Opciones de paginación
per_page_options = [5, 10, 20, 50]


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
    project = Project.objects.first()
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
        "hoy": localtime(),
        'project': project,
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
    

def readings_list(request):
    project = Project.objects.first()
    user = request.user  # usuario en sesión
    query = request.GET.get('q', '')
    page_number = request.GET.get('page', 1)

    per_page_options = [5, 10, 20, 50]
    per_page = int(request.GET.get('per_page', per_page_options[1]))

    today = timezone.localtime().date()

    # Subconsulta: verificar si existe una lectura del mes y año actual para cada acometida
    current_month_reading = Reading.objects.filter(
        connection=OuterRef('pk'),
        date_reading__year=today.year,
        date_reading__month=today.month
    )

    # Base queryset: solo acometidas activas
    connections_list = WaterConnection.objects.filter(is_active=True)

    # Si el usuario es LECTOR o COLECTOR → limitar por comunidad
    if user.groups.filter(name__in=["LECTOR", "COLECTOR"]).exists() and user.community:
        connections_list = connections_list.filter(responsible__community=user.community)

    # Filtros de búsqueda
    connections_list = connections_list.annotate(
        has_current_reading=Exists(current_month_reading),
        current_reading_isPaid=Subquery(current_month_reading.values('isPaid')[:1])
    )

    paginator = Paginator(connections_list, per_page)
    page_obj = paginator.get_page(page_number)

    count_connections = connections_list.count()
    count_readings = connections_list.filter(has_current_reading=True).count()

    context = {
        'reading_search_url': reverse('reading_search'),
        'page_obj': page_obj,
        'per_page': per_page,
        'per_page_options': per_page_options,
        'project': project,
        'today': today,
        'count_connections': count_connections,
        'count_readings': count_readings, 
    }

    if request.headers.get('HX-Request'):
        return render(request, "reading/partials/reading_content.html", context)

    return render(request, "reading/reading.html", context)

def reading_search(request):
    user = request.user
    query = request.GET.get('q', '')
    page_number = request.GET.get('page', 1)

    per_page_options = [5, 10, 20, 50]
    per_page = int(request.GET.get('per_page', per_page_options[1]))

    today = timezone.localtime().date()
    current_month_reading = Reading.objects.filter(
        connection=OuterRef('pk'),
        date_reading__year=today.year,
        date_reading__month=today.month
    )

    connections_list = (
        WaterConnection.objects.filter(is_active=True)
        .annotate(has_current_reading=Exists(current_month_reading))
    )

    if user.groups.filter(name__in=["LECTOR", "COBRADOR"]).exists() and user.community:
        connections_list = connections_list.filter(responsible__community=user.community)

    connections_list_search = connections_list.filter(
        Q(description__icontains=query)
        | Q(responsible__first_name__icontains=query)
        | Q(responsible__last_name__icontains=query)
        | Q(responsible__community__name__icontains=query)
    )

    if not connections_list_search.exists() and query:
        query_lower = query.lower()

        if "registrada" in query_lower:
            connections_list_search = connections_list.filter(has_current_reading=True)
        elif "pendiente" in query_lower:
            connections_list_search = connections_list.filter(has_current_reading=False)


    paginator = Paginator(connections_list_search, per_page)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'reading/partials/readings_table.html',
        {
            'reading_search_url': reverse('reading_search'),
            'page_obj': page_obj,
            'query': query,
            'per_page': per_page,
            'per_page_options': per_page_options,
        }
    )

def reading_create(request, pk):
    con = get_object_or_404(WaterConnection, pk=pk)
    today = timezone.localtime().date()
    project = Project.objects.first()

    result = Reading.calculate_unpaid_total(con)

    pre_reading = 0
    total_to_pay = 0
    months_unread = 0
    total_unpaid = 0
    penalty_fee = 0

    if result:
        last_reading = result["last_reading"]
        pre_reading = last_reading.meter_reading
        total_to_pay = result["total_to_pay"]
        total_unpaid = result["total_unpaid"]
        if total_to_pay is not None:
            total_to_pay = f"{total_to_pay:.2f}"
        else:
            total_to_pay = "0.00"
        months_unread = (today.year - last_reading.date_reading.year) * 12 + (today.month - last_reading.date_reading.month)-1

    
    meeting = Meeting.objects.filter(
        date__year=today.year,
        date__month=today.month
    ).first()

    if meeting:
        attendance_exists = meeting.attendances.filter(partner=con.responsible).exists()
        if not attendance_exists:
            penalty_fee_exists = Reading.objects.filter(
                connection__responsible=con.responsible,
                date_reading__year=today.year,
                date_reading__month=today.month
            ).exists()
            if not penalty_fee_exists:
                penalty_fee = project.absence_fine
                penalty_fee = f"{penalty_fee:.2f}"
        else:
            penalty_fee = "0.00"

    if request.method == "POST":
        form = ReadingForm(request.POST)
        form.instance.connection = con
        form.instance.penalty_fee = Decimal(penalty_fee or "0.00")
        form.instance.late_payment = Decimal(total_to_pay or "0.00")
        form.instance.previous_reading = pre_reading

        if form.is_valid():
            try:
                form.save()
                if request.headers.get('HX-Request'):
                    response = HttpResponse()
                    response["HX-Trigger"] = "readingCreated"
                    return response
            except ValueError as e:
                html = f"""
                <script>
                Swal.fire({{
                    icon: 'error',
                    title: 'Error',
                    text: '{str(e)}',
                    confirmButtonColor: '#3085d6'
                }}).then(() => {{
                    // Cierra la modal Bootstrap correctamente
                    var modalEl = document.getElementById('readingModal');
                    var modalInstance = bootstrap.Modal.getInstance(modalEl);
                    if (modalInstance) {{
                        modalInstance.hide();
                    }}
                }});
                </script>
                """
                return HttpResponse(html)

        else:
            response = render(
                request,
                "reading/partials/reading_form.html",
                {
                    "form": form,
                    "connection": con,
                    "today": today,
                    "pre_reading": pre_reading,
                    "total_to_pay": total_to_pay,
                    "months_unread": months_unread,
                    "total_unpaid": total_unpaid,
                    "penalty_fee": penalty_fee,
                    "penalty": Decimal(penalty_fee),
                },
            )
            response['HX-Retarget'] = 'form'
            response['HX-Reswap'] = 'outerHTML'
            response['HX-Trigger-After-Settle'] = 'fail'
            return response

    else:
        form = ReadingForm()

    return render(
        request,
        "reading/partials/reading_form.html",
        {
            "form": form,
            "connection": con,
            "today": today,
            "pre_reading": pre_reading,
            "total_to_pay": total_to_pay,
            "months_unread": months_unread,
            "total_unpaid": total_unpaid,
            "penalty_fee": penalty_fee,
            "penalty": Decimal(penalty_fee),
        },
    )

def reading_edit(request, pk):
    reading = get_object_or_404(Reading, pk=pk)
    con = reading.connection
    today = reading.date_reading
    project = Project.objects.first()

    result = Reading.calculate_unpaid_total(con)

    total_to_pay = 0
    months_unread = 0
    total_unpaid = 0

    if result:
        last_reading = result["last_reading"]
        total_to_pay = result["total_to_pay"]
        total_unpaid = result["total_unpaid"]
        if total_to_pay is not None:
            total_to_pay = f"{total_to_pay:.2f}"
        else:
            total_to_pay = "0.00"
        months_unread = (today.year - last_reading.date_reading.year) * 12 + (today.month - last_reading.date_reading.month)-1

    if request.method == "POST":
        form = ReadingForm(request.POST, instance=reading)
        if form.is_valid():
            reading.date_reading = None
            form.save()
            if request.headers.get('HX-Request'):
                response = HttpResponse()
                response["HX-Trigger"] = "readingUpdated"
                return response
    else:
        form = ReadingForm(instance=reading)

    return render(
        request,
        "reading/partials/reading_form.html",
        {
            "form": form,
            "reading": reading,
            "connection": con,
            "today": today,
            "pre_reading": reading.previous_reading,
            "total_to_pay": total_to_pay,
            "months_unread": months_unread,
            "total_unpaid": total_unpaid,
            "penalty_fee": f"{reading.penalty_fee:.2f}",
            "penalty": Decimal(reading.penalty_fee or 0),
        },
    )

def reading_view(request, pk):
    reading = get_object_or_404(Reading, pk=pk)
    con = reading.connection
    today = reading.date_reading

    result = Reading.calculate_unpaid_total(con)

    total_to_pay = 0
    months_unread = 0
    total_unpaid = 0

    if result:
        last_reading = result["last_reading"]
        total_to_pay = result["total_to_pay"]
        total_unpaid = result["total_unpaid"]
        if total_to_pay is not None:
            total_to_pay = f"{total_to_pay:.2f}"
        else:
            total_to_pay = "0.00"
        months_unread = (today.year - last_reading.date_reading.year) * 12 + (today.month - last_reading.date_reading.month)-1

    form = ReadingForm(instance=reading)
    for field in form.fields.values():
        field.disabled = True

    return render(
        request,
        "reading/partials/reading_form.html",
        {
            "form": form,
            "reading": reading,
            "connection": con,
            "today": today,
            "pre_reading": reading.previous_reading,
            "total_to_pay": total_to_pay,
            "months_unread": months_unread,
            "total_unpaid": total_unpaid,
            "penalty_fee": f"{reading.penalty_fee:.2f}",
            "penalty": Decimal(reading.penalty_fee or 0),
            "mode": "view",
        },
    )

def reading_details(request):
    """
    Vista que muestra los detalles del cálculo según la tarifa activa,
    los metros consumidos, mora y multa enviados como parámetros.
    """
    from decimal import Decimal

    try:
        metros = Decimal(request.GET.get("metros", 0))
        penalty_fee = Decimal(request.GET.get("penalty_fee", 0))
        late_fee = Decimal(request.GET.get("late_fee", 0))
    except:
        return JsonResponse({"error": "Valores inválidos"}, status=400)

    fee = Fee.objects.filter(isActive=True).first()
    if not fee:
        return JsonResponse({"error": "No hay una tarifa activa"}, status=400)

    try:
        monto = Reading.calculate_amount(fee, metros)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)

    total = monto + penalty_fee + late_fee

    # Buscar el tramo aplicado
    tramo_aplicado = None
    for r in fee.Fee_ranges.all().order_by("min_meter"):
        if r.max_meter is not None:
            if r.min_meter <= metros <= r.max_meter:
                tramo_aplicado = r
                break
        else:
            if metros >= r.min_meter:
                tramo_aplicado = r
                break

    context = {
        "metros": metros,
        "monto": monto,
        "penalty_fee": penalty_fee,
        "late_fee": late_fee,
        "total": total,
        "tramo": tramo_aplicado,
    }
    return render(request, "reading/partials/details_modal.html", context)

def search_connection_reading(request, pk, mode):
    """
    Busca la última lectura de una acometida y redirige según el modo.
    mode: 'edit' o 'view'
    """
    con = get_object_or_404(WaterConnection, pk=pk)
    last_reading = Reading.objects.filter(connection=con).order_by('-date_reading').first()

    if not last_reading:
        # No existe lectura anterior
        raise Http404("No se encontró ninguna lectura para esta acometida.")

    if mode == 'edit':
        url = reverse('reading_edit', args=[last_reading.id])
        response = HttpResponseRedirect(url)
        return response

    elif mode == 'view':
        url = reverse('reading_view', args=[last_reading.id])
        response = HttpResponseRedirect(url)
        return response

    else:
        raise Http404("Modo no válido.")
       

def collection_list(request):
    project = Project.objects.first()
    user = request.user  # usuario en sesión

    page_number = request.GET.get('page', 1)

    per_page_options = [5, 10, 20, 50]
    per_page = int(request.GET.get('per_page', per_page_options[1]))

    today = timezone.localtime().date()
    total_collected = 0

    reading_list = Reading.objects.filter(
        date_reading__year=today.year,
        date_reading__month=today.month
    ).order_by('isPaid')

    # Si el usuario es LECTOR o COLECTOR → limitar por comunidad
    if user.groups.filter(name__in=["LECTOR", "COLECTOR"]).exists() and user.community:
        reading_list = reading_list.filter(connection__responsible__community=user.community)

    data = []
    for reading in reading_list:
        metros = reading.meter_reading - reading.previous_reading 
        total_to_pay = Reading.calculate_amount(reading.fee, metros)
        total_to_pay += reading.late_payment + reading.penalty_fee

        if reading.isPaid:
            total_collected += total_to_pay

        data.append({
            'reading': reading,
            'total_to_pay': total_to_pay
        })

    paginator = Paginator(data, per_page)
    page_obj = paginator.get_page(page_number)

    count_readings = reading_list.count()
    count_collections = reading_list.filter(isPaid=True).count()

    context = {
        'collection_search_url': reverse('collection_search'),
        'page_obj': page_obj,
        'per_page': per_page,
        'per_page_options': per_page_options,
        'project': project,
        'today': today,
        'count_readings': count_readings,
        'count_collections': count_collections,
        'total_collected': total_collected,
    }

    if request.headers.get('HX-Request'):
        return render(request, "collection/partials/collection_content.html", context)

    return render(request, "collection/collection.html", context)

def collection_search(request):
    user = request.user
    query = request.GET.get('q', '').strip()
    page_number = request.GET.get('page', 1)
    mode = request.GET.get('mode', 'month')

    per_page_options = [5, 10, 20, 50]
    per_page = int(request.GET.get('per_page', per_page_options[1]))

    today = timezone.localtime().date()
    current_mode = 'collection/partials/collection_table.html'

    # Filtrar lecturas por mes actual o todas
    if mode == 'all':
        current_mode = 'collection/partials/collection_table_historical.html'
        collection_list = Reading.objects.all()
    else:
        collection_list = Reading.objects.filter(
            date_reading__year=today.year,
            date_reading__month=today.month
        ).order_by('isPaid')

    # Restringir por comunidad si aplica
    if user.groups.filter(name__in=["LECTOR", "COBRADOR"]).exists() and user.community:
        collection_list = collection_list.filter(connection__responsible__community=user.community)

    data = []
    for reading in collection_list:
        metros = reading.meter_reading - reading.previous_reading
        total_to_pay = Reading.calculate_amount(reading.fee, metros)
        total_to_pay += reading.late_payment + reading.penalty_fee

        data.append({
            'reading': reading,
            'total_to_pay': round(total_to_pay, 2),
        })

    # Aplicar búsqueda
    query_lower = query.lower()
    filtered_data = []

    if query:
        for item in data:
            reading = item['reading']
            total_to_pay = item['total_to_pay']

            if (
                query_lower in reading.connection.description.lower()
                or query_lower in reading.receipt_number.lower()
                or query_lower in reading.connection.responsible.first_name.lower()
                or query_lower in reading.connection.responsible.last_name.lower()
                or query_lower in reading.connection.responsible.community.name.lower()
                or query_lower in str(total_to_pay)
            ):
                filtered_data.append(item)

        # Filtros por estado del cobro
        if not filtered_data:
            if "cobrado" in query_lower:
                filtered_data = [item for item in data if item['reading'].isPaid]
            elif "pendiente" in query_lower:
                filtered_data = [item for item in data if not item['reading'].isPaid]
    else:
        filtered_data = data

    # Paginación
    paginator = Paginator(filtered_data, per_page)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        current_mode,
        {
            'collection_search_url': reverse('collection_search'),
            'page_obj': page_obj,
            'query': query,
            'per_page': per_page,
            'per_page_options': per_page_options,
        }
    )

@require_POST
def charge_collected(request, pk):
    reading = get_object_or_404(Reading, pk=pk)

    reading.isPaid = True

    reading.save()

    if request.headers.get("HX-Request"):
        response = collection_list(request)
        response["HX-Trigger"] = (
            "chargedReading"
        )
        return response

    return redirect("collection_list")

def collection_list_historical(request):
    project = Project.objects.first()
    user = request.user  # usuario en sesión

    page_number = request.GET.get('page', 1)

    per_page_options = [5, 10, 20, 50]
    per_page = int(request.GET.get('per_page', per_page_options[1]))

    today = timezone.localtime().date()

    collection_list = Reading.objects.all()

    # Si el usuario es LECTOR o COLECTOR → limitar por comunidad
    if user.groups.filter(name__in=["LECTOR", "COLECTOR"]).exists() and user.community:
        collection_list = collection_list.filter(connection__responsible__community=user.community)

    data = []
    for reading in collection_list:
        metros = reading.meter_reading - reading.previous_reading 
        total_to_pay = Reading.calculate_amount(reading.fee, metros)
        total_to_pay += reading.late_payment + reading.penalty_fee
        data.append({
            'reading': reading,
            'total_to_pay': total_to_pay
        })

    paginator = Paginator(data, per_page)
    page_obj = paginator.get_page(page_number)

    context = {
        'collection_search_url': reverse('collection_search'),
        'page_obj': page_obj,
        'per_page': per_page,
        'per_page_options': per_page_options,
        'project': project,
    }

    if request.headers.get('HX-Request'):
        return render(request, "collection/partials/collection_content_historical.html", context)

    return render(request, "collection/collection_historical.html", context)

def collection_details(request, pk):

    reading = get_object_or_404(Reading, pk=pk)

    result = Reading.calculate_previous_unpaid_total(reading)

    months_unread = 0

    if result:
        last_reading = result["last_reading"]
        if(last_reading):
            months_unread = (reading.date_reading.year - last_reading.date_reading.year) * 12 + (reading.date_reading.month - last_reading.date_reading.month)-1

    meters_consumption = reading.meter_reading - reading.previous_reading
    monto = Reading.calculate_amount(reading.fee, meters_consumption)

    # Buscar el tramo aplicado
    tramo_aplicado = None
    for r in reading.fee.Fee_ranges.all().order_by("min_meter"):
        if r.max_meter is not None:
            if r.min_meter <= meters_consumption <= r.max_meter:
                tramo_aplicado = r
                break
        else:
            if meters_consumption >= r.min_meter:
                tramo_aplicado = r
                break

    context = {
        "reading": reading,
        "months_unread": months_unread,
        "consumption": meters_consumption,
        "monto": monto,
        "total": monto + reading.late_payment + reading.penalty_fee,
        "tramo": tramo_aplicado
    }
    return render(request, "collection/partials/collection_details_modal.html", context)

def collection_pdf(request):
    project = Project.objects.first()
    today = timezone.localtime().date()
    now = timezone.localtime()

    collection_list = Reading.objects.filter(
        date_reading__year=today.year,
        date_reading__month=today.month
    )

    data = []
    for reading in collection_list:
        metros = reading.meter_reading - reading.previous_reading
        total_to_pay = Reading.calculate_amount(reading.fee, metros)
        total_to_pay += reading.late_payment + reading.penalty_fee
        data.append({
            'reading': reading,
            'total_to_pay': total_to_pay
        })

    logo_url = request.build_absolute_uri(project.logo.url) if project.logo else None

    html_string = render_to_string('collection/partials/collection_pdf.html', {
        'project': project,
        'logo_url': logo_url,
        'collection_data': data,
        'today': today,
        'now': now,
    })

    pdf_file = weasyprint.HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Cobros_{today}.pdf"'
    return response