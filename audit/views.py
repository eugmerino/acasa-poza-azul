from django.core.paginator import Paginator
from django.db.models import Q
from django.urls import reverse
from project.models import Partner
from .models import LogEntry
from project.models import Project
from django.shortcuts import render

def logs_list(request):
    project = Project.objects.first()
    query = request.GET.get("q", "")
    page_number = request.GET.get("page", 1)

    per_page_options = [10, 20, 50, 100]
    per_page = int(request.GET.get("per_page", per_page_options[0]))

    logs = LogEntry.objects.select_related("user").order_by("-created_at")

    paginator = Paginator(logs, per_page)
    page_obj = paginator.get_page(page_number)

    context = {
        "logs_search_url": reverse("logs_search"),
        "page_obj": page_obj,
        "query": query,
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

    logs = LogEntry.objects.filter(
        Q(user__username__icontains=q)
        | Q(user__first_name__icontains=q)
        | Q(user__last_name__icontains=q)
        | Q(action__icontains=q)
        | Q(model_name__icontains=q)
        | Q(description__icontains=q)
        | Q(object_id__icontains=q)
        | Q(created_at__icontains=q)
    ).order_by("-created_at")

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
            'per_page': per_page,
            "per_page_options": [10, 20, 50, 100],
            "project": project,
        }
    )

