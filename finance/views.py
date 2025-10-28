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

    paginator = Paginator(transaction_list, per_page)
    page_obj = paginator.get_page(page_number)

    month_start = timezone.localdate().replace(day=1)
    month_end = (month_start + timezone.timedelta(days=32)).replace(day=1) - timezone.timedelta(days=1)

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
        'show_actions': True,  # Asegúrate que esto esté presente
    })

def transaction_list_all(request):
    query = request.GET.get('q', '')
    page_number = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', per_page_options[1]))

    transaction_list = Transaction.objects.all().order_by('-date')

    if query:
        transaction_list = transaction_list.filter(
            Q(concept__icontains=query) |
            Q(type__icontains=query) |
            Q(amount__icontains=query)
        )

    paginator = Paginator(transaction_list, per_page)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "partials/finance/transaction_list_all.html",
        {
            "page_obj": page_obj,
            "transaction_search_all_url": reverse('transaction_search_all'),
            "per_page": per_page,
            "per_page_options": per_page_options,
            "query": query,
            "show_actions": False,
        }
    )



def transaction_search(request):
    query = request.GET.get('q', '')
    page_number = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', per_page_options[1]))

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
            Q(amount__icontains=query)
        )

    paginator = Paginator(transaction_list, per_page)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'partials/finance/transaction_table.html',
        {
            'transaction_search_url': reverse('transaction_search'),
            'page_obj': page_obj,
            'query': query,
            'per_page': per_page,
            'per_page_options': per_page_options,
            'today': now,
            'show_actions': True,  # Añade esta línea
        }
    )

def transaction_search_all(request):
    query = request.GET.get('q', '')
    page_number = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', per_page_options[1]))

    transaction_list = Transaction.objects.all().order_by('-date')

    if query:
        transaction_list = transaction_list.filter(
            Q(concept__icontains=query) |
            Q(type__icontains=query) |
            Q(amount__icontains=query)
        )

    paginator = Paginator(transaction_list, per_page)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'partials/finance/transaction_table.html',
        {
            'page_obj': page_obj,
            'transaction_search_url': reverse('transaction_search_all'),
            'per_page': per_page,
            'per_page_options': per_page_options,
            'query': query,
        }
    )



def transaction_create(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save()
            # Añadir show_actions al contexto
            response = render(request, "partials/finance/transaction_row_table.html", {
                "transaction": transaction,
                "show_actions": True
            })
            response["HX-Trigger"] = json.dumps({
                "state": "success",
                "message": "La transaccion se guardó correctamente"
            })
            return response
        else:
            response = render(request, "partials/finance/transaction_form.html", {"form": form})
            response['HX-Retarget'] = 'form'
            response['HX-Reswap'] = 'outerHTML'
            response['HX-Trigger-After-Settle'] = 'fail'

            return response
    else:
        form = TransactionForm()

    return render(request, "partials/finance/transaction_form.html", {"form": form})

def transaction_edit(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk)

    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            transaction = form.save()
            # Añadir show_actions al contexto
            response = render(request, "partials/finance/transaction_row_table.html", {
                "transaction": transaction,
                "show_actions": True
            })
            response["HX-Trigger"] = json.dumps({
                "state": "success",
                "message": "La transaccion se actualizó correctamente"
            })

            return response
        else:
            response = render(request, "partials/finance/transaction_form.html", {"form": form, "transaction": transaction})
            response['HX-Retarget'] = 'form'
            response['HX-Reswap'] = 'outerHTML'
            response['HX-Trigger-After-Settle'] = 'fail'

            return response
    else:
        form = TransactionForm(instance=transaction)

    return render(
        request,
        "partials/finance/transaction_form.html",
        {"form": form, "transaction": transaction}
    )
