from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.urls import reverse
from .models import Payment
from .forms import PaymentForm
from django.db.models import Q 
from project.models import Project, WaterConnection
from django.http import HttpResponse
import json
from django.db.models import Sum
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.forms.utils import ErrorDict
from django.db import transaction         
from django.contrib import messages 
from django.db.models import Q, CharField, TextField, EmailField
from django.core.paginator import Paginator
from django.utils import timezone
from django.urls import reverse
from django.db import models
from datetime import datetime




WaterConnection = Payment._meta.get_field("connection").remote_field.model
per_page_options = [5, 10, 20, 50]

def payment_list(request):
    today = timezone.localtime().date()
    project = Project.objects.first()  # Obtener el primer proyecto
    query = request.GET.get('q', '')  # Parámetro de búsqueda
    page_number = request.GET.get('page', 1)  # Número de página para paginación
    per_page = int(request.GET.get('per_page', per_page_options[1]))  # Cantidad de elementos por página
    
    # Filtrar los pagos del mes actual
    payment_list = Payment.objects.filter(
        date_pay__year=today.year,
        date_pay__month=today.month,
        ).order_by('-date_pay')

    # Usamos un diccionario para acumular los abonos por cada conexión
    data = []

    for payment in payment_list:
        total_pay = Payment.total_pagado_por_acometida(payment.connection.id)
        data.append({
            'payment': payment,
            'restante': payment.connection.acquisition_price - total_pay 
        })

    # Paginación
    paginator = Paginator(data, per_page)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'payment/payment_connection.html',  # Asegúrate de que este archivo exista
        {
            'payment_search_url': reverse('payment_search'),
            'page_obj': page_obj,
            'query': query,
            'per_page': per_page,
            'per_page_options': per_page_options,
            'project': project,
            'today': today,
        }
    )

def payment_search(request):
    today = timezone.localtime().date()
    query = (request.GET.get('q') or '').strip()
    page_number = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', per_page_options[1]))

    # ----- Helpers dinámicos y seguros -----
    def get_field(model, name):
        try:
            return model._meta.get_field(name)
        except Exception:
            return None

    def str_fields(model):
        """Devuelve nombres de campos de texto comunes (Char/Text/Email)."""
        txt_types = (CharField, TextField, EmailField)
        out = []
        for f in model._meta.get_fields():
            if isinstance(f, txt_types):
                out.append(f.name)
            # Algunos ManyToOneRelation exponen .related_model: los ignoramos aquí
        return set(out)

    def numeric_fields(model):
        num_types = (models.IntegerField, models.FloatField, models.DecimalField, models.BigIntegerField, models.PositiveIntegerField, models.PositiveSmallIntegerField, models.SmallIntegerField)
        return {f.name for f in model._meta.get_fields() if isinstance(f, num_types)}

    def build_icontains_q(prefix, model, candidate_names):
        """Crea un OR Q con los campos de texto existentes."""
        exists = str_fields(model)
        q = Q()
        for name in candidate_names:
            if name in exists:
                q |= Q(**{f"{prefix}{name}__icontains": query})
        return q

    def parse_date(text):
        fmts = ["%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%y", "%d/%m/%y"]
        for f in fmts:
            try:
                return datetime.strptime(text, f).date()
            except ValueError:
                continue
        return None

    # ----- Modelos relacionados (derivados del propio ORM) -----
    ConnectionModel = Payment._meta.get_field('connection').related_model
    # Ajusta este nombre si tu FK no se llama 'responsible'
    responsible_field_name = 'responsible'
    responsible_field = get_field(ConnectionModel, responsible_field_name)
    ResponsibleModel = responsible_field.related_model if responsible_field and hasattr(responsible_field, 'related_model') else None

    # ----- Query base: pagos del mes actual -----
    qs = (
        Payment.objects
        .filter(date_pay__year=today.year, date_pay__month=today.month)
        .select_related('connection', f'connection__{responsible_field_name}')  # evita N+1
    )

    if query:
        tokens = [t for t in query.split() if t]
        big_q = Q()

        # 1) Responsable (todos los campos de texto posibles)
        if ResponsibleModel:
            # nombres típicos que intentaremos si existen
            responsible_text_candidates = [
                'first_name', 'last_name', 'full_name',
                'document', 'dni', 'dui', 'nit', 'nrc',
                'email', 'phone', 'mobile', 'cellphone', 'telefono', 'celular',
                'address', 'direccion', 'sector', 'barrio', 'zona'
            ]
            owner_q = build_icontains_q(f"connection__{responsible_field_name}__", ResponsibleModel, responsible_text_candidates)

            # Soporte "nombre apellido" / "apellido nombre" si hay first_name/last_name
            resp_str = str_fields(ResponsibleModel)
            if len(tokens) >= 2 and {'first_name', 'last_name'} <= resp_str:
                owner_q |= (
                    Q(**{f"connection__{responsible_field_name}__first_name__icontains": tokens[0],
                         f"connection__{responsible_field_name}__last_name__icontains": tokens[1]})
                    |
                    Q(**{f"connection__{responsible_field_name}__first_name__icontains": tokens[-1],
                         f"connection__{responsible_field_name}__last_name__icontains": tokens[0]})
                )
            big_q |= owner_q

        # 2) Conexión (campos de texto comunes)
        connection_text_candidates = [
            'description', 'code', 'codigo', 'address', 'direccion',
            'sector', 'barrio', 'zona', 'meter_number', 'medidor', 'lot', 'lote'
        ]
        big_q |= build_icontains_q("connection__", ConnectionModel, connection_text_candidates)

        # 3) Monto si es número
        amt_q = Q()
        try:
            # admite "100", "100.50" (coma no, pero puedes agregarla)
            if query.replace('.', '', 1).isdigit():
                amount_val = float(query)
                amt_q = Q(amount=amount_val)
        except Exception:
            pass
        big_q |= amt_q

        # 4) ID/PK de conexión o pago si es entero
        if query.isdigit():
            big_q |= Q(pk=int(query)) | Q(connection__pk=int(query))

        # 5) Fecha exacta (si el texto parece fecha)
        date_val = parse_date(query)
        if date_val:
            big_q |= Q(date_pay=date_val)

        qs = qs.filter(big_q)

    qs = qs.order_by('-date_pay')

    # ----- Armado de data con 'restante' como en payment_list -----
    data = []
    for payment in qs:
        total_pay = Payment.total_pagado_por_acometida(payment.connection_id)
        data.append({
            'payment': payment,
            'restante': payment.connection.acquisition_price - total_pay
        })

    paginator = Paginator(data, per_page)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'payment/partials/payment_table.html',
        {
            'payment_search_url': reverse('payment_search'),
            'page_obj': page_obj,
            'query': query,
            'per_page': per_page,
            'per_page_options': per_page_options,
        }
    )

def payment_list_view(request):
    project = Project.objects.first()  # Suponiendo que tienes un modelo 'Project' similar a lo que usas para 'Directive'
    query = request.GET.get('q', '')  # Para búsqueda
    page_number = request.GET.get('page', 1)  # Número de página para paginación
    per_page = int(request.GET.get('per_page', per_page_options[1]))  # Cantidad de elementos por página

    # Obtener todos los pagos y ordenarlos por fecha de pago
    payment_list = Payment.objects.all().order_by('-date_pay')

    data = []

    for payment in payment_list:
        total_pay = Payment.total_pagado_por_acometida(payment.connection.id)
        data.append({
            'payment': payment,
            'restante': payment.connection.acquisition_price - total_pay 
        })

    # Paginación
    paginator = Paginator(data, per_page)
    page_obj = paginator.get_page(page_number)
    
    return render(
        request,
        'payment/payment_connection_view.html',  # Asegúrate de que este archivo exista en 'payment/partials/'
        {
            'payment_view_search_url': reverse('payment_search_view'),
            'page_obj': page_obj,
            'query': query,
            'per_page': per_page,
            'per_page_options': per_page_options,
            'project': project,
        }
    ) 

def payment_search_view(request):
    query = request.GET.get('q', '')  # Buscar por monto o conexión (esto depende de lo que tengas en tu modelo)
    page_number = request.GET.get('page', 1)  # Número de página para paginación
    per_page = int(request.GET.get('per_page', per_page_options[1]))  # Cantidad de elementos por página

    # Filtrar los pagos según el monto o la descripción de la conexión
    payment_list = Payment.objects.filter(
        Q(amount__icontains=query) |
        Q(connection__description__icontains=query)  # Buscar por 'description' de la conexión
    ).order_by('-date_pay')


    accumulated_payments = {}
    for payment in payment_list:
        connection_id = payment.connection.id  # Obtener el id de la conexión

        if connection_id not in accumulated_payments:
            # Si no hay abonos previos para esta conexión, el "Restante" será el precio de adquisición
            accumulated_payments[connection_id] = payment.connection.acquisition_price

        # Restamos el abono actual al "Restante" de esta conexión
        accumulated_payments[connection_id] -= payment.amount

        # Asignamos el "Restante" calculado al pago actual
        payment.restante = accumulated_payments[connection_id]

    # Paginación
    paginator = Paginator(payment_list, per_page)
    page_obj = paginator.get_page(page_number)


    return render(
        request,
        'payment/partials/payment_table_view.html',  # Asegúrate de que este archivo exista en 'payment/partials/'
        {
            'payment_view_search_url': reverse('payment_search_view'),
            'page_obj': page_obj,
            'query': query,
            'per_page': per_page,
            'per_page_options': per_page_options,
        }
    )

def payment_create(request):
    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    pay = form.save(commit=False)
                    # Dispara las validaciones del modelo (acometida saldada / sobrepago)
                    pay.full_clean()
                    pay.save()
            except ValidationError as e:
                # Poner los errores en el form para re-renderizarlo con mensajes
                if hasattr(e, "message_dict"):
                    for field, msgs in e.message_dict.items():
                        for m in msgs:
                            form.add_error(field if field != "__all__" else None, m)
                else:
                    form.add_error(None, str(e))

                if request.headers.get("HX-Request"):
                    # Mensaje amigable para SweetAlert
                    msg = "No se pudo guardar el pago."
                    conn_err = form.errors.get("connection", [])
                    amount_err = form.errors.get("amount", [])
                    if conn_err:
                        msg = conn_err[0]
                    elif amount_err:
                        msg = amount_err[0]

                    resp = render(request, "payment/partials/payment_form.html", {"form": form})
                    resp["HX-Retarget"] = "#payment-form"
                    resp["HX-Reswap"] = "outerHTML"
                    resp["HX-Trigger"] = json.dumps({"payment:error": {"msg": msg}})
                    resp.status_code = 422
                    return resp

                # Petición normal (sin HTMX)
                return render(request, "payment/partials/payment_form.html", {"form": form})

            # Éxito
            if request.headers.get("HX-Request"):
                resp = render(
                    request,
                    "payment/partials/payment_row_table.html",  # <-- devuelve un <tr>
                    {"pay": pay},
                )
                resp["HX-Trigger-After-Swap"] = json.dumps(
                    {"payment:added": {"id": pay.id, "msg": "El pago se guardó correctamente."}}
                )
                return resp

            return redirect("payment_create_success")

        # Form inválido por otros motivos (requeridos, formato, etc.)
        if request.headers.get("HX-Request"):
            msg = "Revisa los campos."
            conn_err = form.errors.get("connection", [])
            amount_err = form.errors.get("amount", [])
            if conn_err:
                msg = conn_err[0]
            elif amount_err:
                msg = amount_err[0]

            resp = render(request, "payment/partials/payment_form.html", {"form": form})
            resp["HX-Retarget"] = "#payment-form"
            resp["HX-Reswap"] = "outerHTML"
            resp["HX-Trigger-After-Swap"] = json.dumps({"payment:error": {"msg": msg}})
            return resp

    # GET
    form = PaymentForm()
    return render(request, "payment/partials/payment_form.html", {"form": form})
    
def payment_connection_search(request):
    """
    Devuelve las coincidencias de acometidas para el autocomplete (HTMX).
    El parámetro del input es 'connection_search'.
    """
    q = request.GET.get("connection_search", "").strip()
    results = WaterConnection.objects.all()

    if q:
        
        results = results.filter(
            Q(description__icontains=q) |
            Q(responsible__first_name__icontains=q) |
            Q(responsible__last_name__icontains=q)
         )[:3]

    return render(
         request,
         "payment/partials/payment_search_results.html",  
         {"connections": results},
    )


def payment_create_success(request):
    return render(request, 'payment/partials/payment_create_success.html') 