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


per_page_options =[5, 10, 20, 50]

def transaction_list(request):
    transaction = Transaction.objects.first()
    query = request.GET.get('q', '')
    page_number = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', per_page_options[1]))

    transaction_list = Transaction.objects.all().order_by('-date')
    paginator = Paginator(transaction_list, per_page)
    page_obj = paginator.get_page(page_number)

    now = timezone.localtime()

    return render(
        request,
        'finance/transaccion.html',
        {
            'transaction_search_url': reverse('transaction_search'),
            'page_obj': page_obj,
            'query': query,
            'per_page': per_page,
            'per_page_options': per_page_options,
            'form': TransactionForm(),
            'today': now.date(),
        }
    )

def transaction_search(request):
    query = request.GET.get('q', '')
    page_number = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', per_page_options[1]))

    transaction_list = Transaction.objects.filter(
        Q(concept__icontains=query) |
        Q(type__icontains=query) |
        Q(amount__icontains=query)
    ).order_by('-date')

    paginator = Paginator(transaction_list, per_page)
    page_obj = paginator.get_page(page_number)

    now = timezone.localtime()

    return render(
        request,
        'partials/finance/transaction_table.html',
        {
           'transaction_search_url': reverse('transaction_search'),
            'page_obj': page_obj,
            'query': query,
            'per_page': per_page,
            'per_page_options': per_page_options,
            'today': timezone.localdate(),
            'current_time': localtime(now).time(),
        }
    )

def transaction_create(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save()
            return render(request, "partials/finance/transaction_row_table.html", {"transaction": transaction})
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

    return redirect(request, "partials/finance/transaction_form.html", {"form": form})

def transaction_edit(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk)

    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            transaction = form.save()
            response = render(request, "partials/finance/transaction_row_table.html", {"transaction": transaction})
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
