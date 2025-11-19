from django.core.paginator import Paginator
from django.db.models import Q
from django.urls import reverse
from project.models import Partner
from .models import LogEntry
from project.models import Project
from django.shortcuts import render
from django.utils import timezone
from datetime import datetime, timedelta


def logs_list(request):
    project = Project.objects.first()
    query = request.GET.get("q", "")
    page_number = request.GET.get("page", 1)
    action_filter = request.GET.get("action", "")
    start_date = request.GET.get("start_date", "")
    end_date = request.GET.get("end_date", "")

    per_page_options = [10, 20, 50, 100]
    per_page = int(request.GET.get("per_page", per_page_options[0]))

    logs = LogEntry.objects.select_related("user").order_by("-created_at")
    
    # Aplicar filtros
    if action_filter:
        logs = logs.filter(action=action_filter)
    
    if start_date:
        try:
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            logs = logs.filter(created_at__date__gte=start_datetime.date())
        except ValueError:
            pass
    
    if end_date:
        try:
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
            # Incluir todo el día final
            end_datetime = end_datetime + timedelta(days=1) - timedelta(seconds=1)
            logs = logs.filter(created_at__date__lte=end_datetime.date())
        except ValueError:
            pass

    paginator = Paginator(logs, per_page)
    page_obj = paginator.get_page(page_number)

    context = {
        "logs_search_url": reverse("logs_search"),
        "page_obj": page_obj,
        "query": query,
        "action_filter": action_filter,
        "start_date": start_date,
        "end_date": end_date,
        "per_page": per_page,
        "per_page_options": per_page_options,
        "project": project,
    }

    if request.headers.get("HX-Request"):
        return render(request, "logs/partials/logs_content.html", context)

    return render(request, "logs/logs.html", context)

def logs_search(request):
    project = Project.objects.first()
    q = request.GET.get("q", "")
    page_number = request.GET.get("page", 1)
    action_filter = request.GET.get("action", "")
    start_date = request.GET.get("start_date", "")
    end_date = request.GET.get("end_date", "")

    logs = LogEntry.objects.all()
    
    # Filtro de búsqueda general
    if q:
        logs = logs.filter(
            Q(user__username__icontains=q)
            | Q(user__first_name__icontains=q)
            | Q(user__last_name__icontains=q)
            | Q(action__icontains=q)
            | Q(model_name__icontains=q)
            | Q(description__icontains=q)
            | Q(object_id__icontains=q)
            | Q(created_at__icontains=q)
        )
    
    # Filtro por acción
    if action_filter:
        logs = logs.filter(action=action_filter)
    
    # Filtro por fecha desde
    if start_date:
        try:
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            logs = logs.filter(created_at__date__gte=start_datetime.date())
        except ValueError:
            pass
    
    # Filtro por fecha hasta
    if end_date:
        try:
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
            # Incluir todo el día final
            end_datetime = end_datetime + timedelta(days=1) - timedelta(seconds=1)
            logs = logs.filter(created_at__date__lte=end_datetime.date())
        except ValueError:
            pass

    logs = logs.order_by("-created_at")

    per_page = int(request.GET.get("per_page", 10))
    paginator = Paginator(logs, per_page)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'logs/partials/logs_table.html',
        {
            'logs_search_url': reverse('logs_search'),
            'page_obj': page_obj,
            'query': q,
            'action_filter': action_filter,
            'start_date': start_date,
            'end_date': end_date,
            'per_page': per_page,
            "per_page_options": [10, 20, 50, 100],
            "project": project,
        }
    )

