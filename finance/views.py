# Importaciones de Python estándar
import calendar
import json
from datetime import datetime

# Importaciones de Django
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import models, transaction
from django.db.models import Sum, Q
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import localtime, now
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods

# Importaciones de terceros
import weasyprint

# Importaciones locales
from project.models import Project, WaterConnection
from .forms import PaymentForm, TransactionForm
from .models import Payment, Transaction

# Constantes
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
        total_pay = Payment.total_pagado_por_acometida(payment)
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
    query = request.GET.get('q', '')  # Buscar por monto o conexión (esto depende de lo que tengas en tu modelo)
    page_number = request.GET.get('page', 1)  # Número de página para paginación
    per_page = int(request.GET.get('per_page', per_page_options[1]))  # Cantidad de elementos por página

    # Filtramos los pagos actuales y por la buscada
    payment_list = (
        Payment.objects.filter(
            date_pay__year=today.year,
            date_pay__month=today.month,
        )
        .filter(
            Q(connection__description__icontains=query)
            | Q(connection__responsible__first_name__icontains=query)
            | Q(connection__responsible__last_name__icontains=query)
        )
        .order_by('-date_pay')
    )

    # Usamos un diccionario para acumular los abonos por cada conexión
    data = []

    for payment in payment_list:
        total_pay = Payment.total_pagado_por_acometida(payment)
        data.append({
            'payment': payment,
            'restante': payment.connection.acquisition_price - total_pay 
        })

    # Paginación
    paginator = Paginator(data, per_page)
    page_obj = paginator.get_page(page_number)


    return render(
        request,
        'payment/partials/payment_table.html',  # Asegúrate de que este archivo exista en 'payment/partials/'
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
        total_pay = Payment.total_pagado_por_acometida(payment)
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
        Q(amount__icontains=query) 
        | Q(connection__description__icontains=query)
        | Q(connection__responsible__first_name__icontains=query)
        | Q(connection__responsible__last_name__icontains=query)
    ).order_by('-date_pay')

    # Usamos un diccionario para acumular los abonos por cada conexión
    data = []

    for payment in payment_list:
        total_pay = Payment.total_pagado_por_acometida(payment)
        data.append({
            'payment': payment,
            'restante': payment.connection.acquisition_price - total_pay 
        })

    # Paginación
    paginator = Paginator(data, per_page)
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


from django.shortcuts import render
from .models import Transaction
from .forms import TransactionForm
from django.shortcuts import get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import localtime, now
import json

per_page_options =[5, 10, 20, 50]

def transaction_list(request):
    query = request.GET.get('q', '')
    page_number = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', per_page_options[1]))
    selected_month = request.GET.get('month', '')

    now = timezone.localtime()
    current_year = now.year
    current_month = now.month

    # Si no hay mes seleccionado, usar mes actual
    if not selected_month:
        selected_month = f"{current_year}-{current_month:02d}"

    try:
        year, month = map(int, selected_month.split('-'))
        transaction_list = Transaction.objects.filter(date__year=year, date__month=month).order_by('-date')
    except ValueError:
        transaction_list = Transaction.objects.all().order_by('-date')

    # Filtro de búsqueda
    if query:
        transaction_list = transaction_list.filter(
            Q(concept__icontains=query) |
            Q(type__icontains=query) |
            Q(amount__icontains=query)
        )

    # Totales
    total_ingresos = transaction_list.filter(type='I').aggregate(Sum('amount'))['amount__sum'] or 0
    total_egresos = transaction_list.filter(type='E').aggregate(Sum('amount'))['amount__sum'] or 0

    paginator = Paginator(transaction_list, per_page)
    page_obj = paginator.get_page(page_number)

    month_start = timezone.localdate().replace(day=1)
    month_end = (month_start + timezone.timedelta(days=32)).replace(day=1) - timezone.timedelta(days=1)

    # Calcular totales del mes actual
    total_income = transaction_list.filter(type='I').aggregate(
        total=Sum('amount'))['total'] or 0
    total_expenses = transaction_list.filter(type='E').aggregate(
        total=Sum('amount'))['total'] or 0
    balance = total_income - total_expenses

    return render(request, 'finance/transaccion.html', {
        'transaction_search_url': reverse('transaction_search'),
        'page_obj': page_obj,
        'query': query,
        'per_page': per_page,
        'per_page_options': per_page_options,
        'form': TransactionForm(),
        'today': timezone.localdate(),
        'month_start': month_start,
        'month_end': month_end,
        'selected_month': selected_month,
        'show_actions': True,
        'total_income': total_income,  # Cambiado de total_ingresos
        'total_expenses': total_expenses,  # Cambiado de total_egresos
        'balance': balance,  # Añadido el balance
        'is_management': True,
    })


def transaction_list_all(request):
    query = request.GET.get('q', '')
    page_number = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', per_page_options[1]))

    today = timezone.localtime().date()

    qs = Transaction.objects.all().order_by('-date')
    if query:
        qs = qs.filter(
            Q(concept__icontains=query) |
            Q(type__icontains=query) |
            Q(amount__icontains=query)
        )

    # Totales sobre el queryset filtrado (no solo la página)
    total_income = qs.filter(type='I').aggregate(total=Sum('amount'))['total'] or 0
    total_expenses = qs.filter(type='E').aggregate(total=Sum('amount'))['total'] or 0
    balance = total_income - total_expenses

    paginator = Paginator(qs, per_page)
    page_obj = paginator.get_page(page_number)

    return render(request, 'finance/partials/transaction_list_all.html', {
        'page_obj': page_obj,
        'transaction_search_all_url': reverse('transaction_search_all'),
        'per_page': per_page,
        'per_page_options': per_page_options,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'balance': balance,
        'query': query,
        'today': today,
        'is_management': False,
    })



def transaction_search(request):
    query = request.GET.get('q', '')
    page_number = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', per_page_options[1]))

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    type_filter = request.GET.get('type')
    now = timezone.localdate()
    current_year = now.year
    current_month = now.month

    # Filtrar solo transacciones del mes actual
    transaction_list = Transaction.objects.filter(
        date__year=current_year,
        date__month=current_month
    ).order_by('-date')

    # Filtro de búsqueda
    if query:
        transaction_list = transaction_list.filter(
            Q(concept__icontains=query) |
            Q(type__icontains=query) |
            Q(amount__icontains=query)|
            Q(date__icontains=query)
        )

    paginator = Paginator(transaction_list, per_page)
    page_obj = paginator.get_page(page_number)

    # Calcular totales
    total_income = transaction_list.filter(type='I').aggregate(
        total=Sum('amount'))['total'] or 0
    total_expenses = transaction_list.filter(type='E').aggregate(
        total=Sum('amount'))['total'] or 0
    balance = total_income - total_expenses

    return render(
        request,
        'finance/partials/transaction_table.html',
        {
            'transaction_search_url': reverse('transaction_search'),
            'page_obj': page_obj,
            'query': query,
            'per_page': per_page,
            'per_page_options': per_page_options,
            'today': now,
            'show_actions': True,  # Añade esta línea
            'total_income': total_income,
            'total_expenses': total_expenses,
            'balance': balance,
            'is_management': True,
        }
    )

def transaction_search_all(request):
    query = request.GET.get('q', '')
    page_number = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', per_page_options[1]))

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    type_filter = request.GET.get('type')
    transaction_list = Transaction.objects.all().order_by('-date')

    if query:
        transaction_list = transaction_list.filter(
            Q(concept__icontains=query) |
            Q(type__icontains=query) |
            Q(amount__icontains=query)|
            Q(date__icontains=query)
        )

    # Calcular totales
    total_income = transaction_list.filter(type='I').aggregate(
        total=Sum('amount'))['total'] or 0
    total_expenses = transaction_list.filter(type='E').aggregate(
        total=Sum('amount'))['total'] or 0
    balance = total_income - total_expenses

    paginator = Paginator(transaction_list, per_page)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'finance/partials/transaction_table.html',
        {
            'page_obj': page_obj,
            'transaction_search_url': reverse('transaction_search_all'),
            'per_page': per_page,
            'per_page_options': per_page_options,
            'query': query,
            'total_income': total_income,
            'total_expenses': total_expenses,
            'balance': balance,
            'show_actions': False,  # 👈 Ahora falso
            'is_management': False,
        }
    )

def transaction_create(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save()
            
            # Recalcular totales
            now = timezone.localtime()
            transactions = Transaction.objects.filter(
                date__year=now.year,
                date__month=now.month
            )
            total_income = transactions.filter(type='I').aggregate(
                total=Sum('amount'))['total'] or 0
            total_expenses = transactions.filter(type='E').aggregate(
                total=Sum('amount'))['total'] or 0
            balance = total_income - total_expenses

            response = render(request, "finance/partials/transaction_table.html", {
                'page_obj': Paginator(transactions, per_page_options[1]).get_page(1),
                'total_income': total_income,
                'total_expenses': total_expenses,
                'balance': balance,
                'show_actions': True
            })
            response["HX-Trigger"] = json.dumps({
                "state": "success",
                "message": "La transacción se guardó correctamente",
                "transactionChanged": True
            })
            return response
        else:
            response = render(request, "finance/partials/transaction_form.html", {"form": form})
            response['HX-Retarget'] = 'form'
            response['HX-Reswap'] = 'outerHTML'
            response['HX-Trigger-After-Settle'] = 'fail'

            return response
    else:
        form = TransactionForm()

    return render(request, "finance/partials/transaction_form.html", {"form": form})

def transaction_edit(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk)

    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            transaction = form.save()
            
            # Recalcular totales después de editar
            now = timezone.localdate()
            transaction_list = Transaction.objects.filter(
                date__year=now.year,
                date__month=now.month
            )
            total_income = transaction_list.filter(type='I').aggregate(
                total=Sum('amount'))['total'] or 0
            total_expenses = transaction_list.filter(type='E').aggregate(
                total=Sum('amount'))['total'] or 0
            balance = total_income - total_expenses

            response = render(request, "finance/partials/transaction_row_table.html", {
                "transaction": transaction,
                "show_actions": True,
                "total_income": total_income,
                "total_expenses": total_expenses,
                "balance": balance,
            })
            response["HX-Trigger"] = json.dumps({
                "state": "success",
                "message": "La transaccion se actualizó correctamente",
                "transactionChanged": True
            })

            return response
        else:
            response = render(request, "finance/partials/transaction_form.html", {"form": form, "transaction": transaction})
            response['HX-Retarget'] = 'form'
            response['HX-Reswap'] = 'outerHTML'
            response['HX-Trigger-After-Settle'] = 'fail'

            return response
    else:
        form = TransactionForm(instance=transaction)

    return render(
        request,
        "finance/partials/transaction_form.html",
        {"form": form, "transaction": transaction}
    )

def transaction_pdf(request):
    project = Project.objects.first()
    logo_url = request.build_absolute_uri(project.logo.url) if project.logo else None

    # Obtener parámetro ?month=YYYY-MM
    month_param = request.GET.get('month')
    

    if month_param:
        try:
            selected_date = datetime.strptime(month_param, '%Y-%m')
            year = selected_date.year
            month = selected_date.month
        except ValueError:
            # Si el formato es incorrecto, usar el mes actual
            today = timezone.localtime().date()
            year = today.year
            month = today.month
    else:
        # Si no se pasa parámetro, usar el mes actual
        today = timezone.localtime().date()
        year = today.year
        month = today.month
     
    month_name = _(calendar.month_name[month]).capitalize()
    # 🔒 Filtro estricto por año y mes seleccionados
    transactions = Transaction.objects.filter(
        date__year=year,
        date__month=month
    ).order_by('date')

    # Calcular totales solo de esas transacciones
    total_income = transactions.filter(type='I').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expenses = transactions.filter(type='E').aggregate(Sum('amount'))['amount__sum'] or 0
    balance = total_income - total_expenses

    # Fechas actuales
    today = timezone.localtime().date()
    now = timezone.localtime()

    # Renderizar HTML
    html_string = render_to_string('finance/partials/transaction_pdf.html', {
        'project': project,
        'logo_url': logo_url,
        'transactions': transactions,
        'today': today,
        'now': now,
        'month': month,
        'year': year,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'balance': balance,
        'month_name': month_name,
    })

    pdf_file = weasyprint.HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Transacciones_{year}_{month}.pdf"'
    return response