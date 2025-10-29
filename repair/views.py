from django.shortcuts import render
from project.models import Project
from .models import Repair
from .forms import ReportForm, RepairForm, RepairPayForm
from django.core.paginator import Paginator
from django.urls import reverse
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

# Opciones de paginación
per_page_options = [5, 10, 20, 50]

def report_repair_list(request):
    project = Project.objects.first()

    page_number = request.GET.get('page', 1)

    per_page = int(request.GET.get('per_page', per_page_options[1]))

    report_list = Repair.objects.filter(repair_date__isnull=True).order_by('-report_date')

    paginator = Paginator(report_list, per_page)
    page_obj = paginator.get_page(page_number)

    context = {
        'report_repair_search_url': reverse('report_repair_search'),
        'page_obj': page_obj,
        'per_page': per_page,
        'per_page_options': per_page_options,
        'project': project,
    }

    # Si la petición viene de HTMX => renderiza solo el contenido parcial
    if request.headers.get('HX-Request'):
        return render(request, "report_repair/partials/report_repair_content.html", context)

    # Si es petición normal => renderiza toda la página
    return render(request, "report_repair/report_repair.html", context)

def report_repair_search(request):
    query = request.GET.get('q', '') 
    page_number = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', per_page_options[1]))

    report_list = Repair.objects.filter(
        Q(report_title__icontains=query)
        | Q(community__name__icontains=query)
    ).order_by('-report_date')

    paginator = Paginator(report_list, per_page)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'report_repair/partials/report_repair_table.html',
        {
            'report_repair_search_url': reverse('report_repair_search'),
            'page_obj': page_obj,
            'query': query,
            'per_page': per_page,
            'per_page_options': per_page_options,
        }
    )

def report_repair_create(request):
    if request.method == "POST":
        form = ReportForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            if request.headers.get('HX-Request'):
                response = report_repair_list(request)
                response["HX-Trigger"] = "reportRepairCreated"
                return response
            return redirect('report_repair_list')
        else:
            response = render(
                request,
                "report_repair/partials/report_repair_form.html",
                {"form": form, "mode": "create"}
            )
            response['HX-Target'] = '#main-container'
            response['HX-Swap'] = 'innerHTML'
            response['HX-Trigger-After-Settle'] = 'fail'
            return response
    else: 
        form = ReportForm()
    return render(
        request,
        "report_repair/partials/report_repair_form.html",
        {"form": form, "mode": "create"}
    )

def report_repair_edit(request, pk):
    report = get_object_or_404(Repair, pk=pk)

    if request.method == "POST":
        form = ReportForm(request.POST, request.FILES, instance=report)

        if form.is_valid():
            form.save()
            if request.headers.get("HX-Request"):
                response = report_repair_list(request)
                response["HX-Trigger"] = "reportRepairEdited"
                return response
            return redirect("report_repair_list")
        else:
            response = render(
                request,
                "report_repair/partials/report_repair_form.html",
                {"form": form, "mode": "edit", "report": report},
            )
            response['HX-Target'] = '#main-container'
            response['HX-Swap'] = 'innerHTML'
            response['HX-Trigger-After-Settle'] = 'fail'
            return response
    else:
        form = ReportForm(instance=report)

    return render(
        request,
        "report_repair/partials/report_repair_form.html",
        {"form": form, "mode": "edit", "report": report},
    )

def report_repair_delete(request, pk):
    report = get_object_or_404(Repair, pk=pk)

    if request.method == "POST":
        report.delete()

        if request.headers.get("HX-Request"):
            from .views import report_repair_list
            response = report_repair_list(request)
            response["HX-Trigger"] = "reportRepairDeleted"
            return response

        return redirect("report_repair_list")

    # Para GET, redirigir directamente
    return redirect("report_repair_list")

def report_repair_view(request, pk):
    report = get_object_or_404(Repair, pk=pk)
    form = ReportForm(instance=report)
    for field in form.fields.values():
        field.disabled = True
    return render(request, "report_repair/partials/report_repair_form.html", {"form": form, "mode": "view", "report": report})


def repair_list(request):
    project = Project.objects.first()

    page_number = request.GET.get('page', 1)

    per_page = int(request.GET.get('per_page', per_page_options[1]))

    repair_list = Repair.objects.all().order_by('-report_date')

    paginator = Paginator(repair_list, per_page)
    page_obj = paginator.get_page(page_number)

    context = {
        'repair_search_url': reverse('repair_search'),
        'page_obj': page_obj,
        'per_page': per_page,
        'per_page_options': per_page_options,
        'project': project,
    }

    # Si la petición viene de HTMX => renderiza solo el contenido parcial
    if request.headers.get('HX-Request'):
        return render(request, "repair/partials/repair_content.html", context)

    # Si es petición normal => renderiza toda la página
    return render(request, "repair/repair.html", context)

def repair_search(request):
    query = request.GET.get('q', '') 
    page_number = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', per_page_options[1]))

    repair_list = Repair.objects.filter(
        Q(report_title__icontains=query)
        | Q(community__name__icontains=query)
    ).order_by('-report_date')

    paginator = Paginator(repair_list, per_page)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'repair/partials/repair_table.html',
        {
            'repair_search_url': reverse('repair_search'),
            'page_obj': page_obj,
            'query': query,
            'per_page': per_page,
            'per_page_options': per_page_options,
        }
    )

def repair_edit(request, pk):
    report = get_object_or_404(Repair, pk=pk)
    today = timezone.localtime().date()

    if request.method == "POST":

        data = request.POST.copy()
        data["repair_date"] = today.strftime("%Y-%m-%d")

        form = RepairForm(data, request.FILES, instance=report)

        if form.is_valid():
            form.save()
            if request.headers.get("HX-Request"):
                response = repair_list(request)
                response["HX-Trigger"] = "repairEdited"
                return response
            return redirect("repair_list")
        else:
            response = render(
                request,
                "repair/partials/repair_form.html",
                {"form": form, "mode": "edit", "report": report, "today": today},
            )
            response['HX-Target'] = '#main-container'
            response['HX-Swap'] = 'innerHTML'
            response['HX-Trigger-After-Settle'] = 'fail'
            return response
    else:
        form = RepairForm(instance=report)

    return render(
        request,
        "repair/partials/repair_form.html",
        {"form": form, "report": report, "today": today},
    )


def repair_pay_list(request):
    project = Project.objects.first()

    page_number = request.GET.get('page', 1)

    per_page = int(request.GET.get('per_page', per_page_options[1]))

    repair_list = Repair.objects.filter(repair_date__isnull=False).order_by('is_paid', '-repair_date')

    paginator = Paginator(repair_list, per_page)
    page_obj = paginator.get_page(page_number)

    context = {
        'repair_pay_search_url': reverse('repair_pay_search'),
        'page_obj': page_obj,
        'per_page': per_page,
        'per_page_options': per_page_options,
        'project': project,
    }

    # Si la petición viene de HTMX => renderiza solo el contenido parcial
    if request.headers.get('HX-Request'):
        return render(request, "repair/partials/repair_pay_content.html", context)

    # Si es petición normal => renderiza toda la página
    return render(request, "repair/repair_pay.html", context)

def repair_pay_search(request):
    query = request.GET.get('q', '') 
    page_number = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', per_page_options[1]))

    repair_list = Repair.objects.filter(
        Q(report_title__icontains=query) |
        Q(community__name__icontains=query),
        repair_date__isnull=False
    ).order_by('is_paid', '-repair_date')

    paginator = Paginator(repair_list, per_page)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'repair/partials/repair_pay_table.html',
        {
            'repair_pay_search_url': reverse('repai_pay_search'),
            'page_obj': page_obj,
            'query': query,
            'per_page': per_page,
            'per_page_options': per_page_options,
        }
    )

def repair_pay_edit(request, pk):
    report = get_object_or_404(Repair, pk=pk)
    today = timezone.localtime().date()

    if request.method == "POST":

        data = request.POST.copy()
        data["payment_date"] = today.strftime("%Y-%m-%d")

        form = RepairPayForm(data, request.FILES, instance=report)

        if form.is_valid():
            form.save()
            if request.headers.get("HX-Request"):
                response = repair_pay_list(request)
                response["HX-Trigger"] = "repairPayEdited"
                return response
            return redirect("repair_pay_list")
        else:
            response = render(
                request,
                "repair/partials/repair_pay_form.html",
                {"form": form, "report": report, "today": today},
            )
            response['HX-Target'] = '#main-container'
            response['HX-Swap'] = 'innerHTML'
            response['HX-Trigger-After-Settle'] = 'fail'
            return response
    else:
        form = RepairPayForm(instance=report)

    return render(
        request,
        "repair/partials/repair_pay_form.html",
        {"form": form, "report": report, "today": today},
    )