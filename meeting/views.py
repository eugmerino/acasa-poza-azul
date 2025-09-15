from django.shortcuts import render
from .models import Meeting
from project.models import Project
from django.db.models import Q
from django.core.paginator import Paginator
from django.urls import reverse
from meeting.forms import MeetingForm
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
import json


per_page_options = [5, 10, 20, 50]

def meet_list(request):
    project = Project.objects.first()
    query = request.GET.get('q', '') 
    page_number = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', per_page_options[1]))

    meet_list = Meeting.objects.all().order_by('-isActive')
    paginator = Paginator(meet_list, per_page)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'reuniones.html',
        {
            'meet_search_url': reverse('meet_search'),
            'page_obj': page_obj,
            'query': query,
            'per_page': per_page,
            'per_page_options': per_page_options,
            'form': MeetingForm(),
            'project': project,
        }
    )


def meet_search(request):
    query = request.GET.get('q', '') 
    page_number = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', per_page_options[1]))

    meet_list = Meeting.objects.filter(
        Q(title__icontains=query) | Q(date__icontains=query)
    ).order_by('-isActive')

    paginator = Paginator(meet_list, per_page)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'partials/meet_table.html',
        {
            'meet_search_url': reverse('meet_search'),
            'page_obj': page_obj,
            'query': query,
            'per_page': per_page,
            'per_page_options': per_page_options,
        }
    )

def meet_create(request):
    if request.method == "POST":
        form = MeetingForm(request.POST)
        if form.is_valid():
            meeting = form.save()
            response = render(request, "partials/meet_row_table.html", {"meeting": meeting})
            response["HX-Trigger"] = json.dumps({
                "state": "success",
                "message": "La reunión se guardó correctamente"
            })

            return response
        else:
            response = render(request, "partials/meet_form.html", {"form": form})
            response['HX-Retarget'] = 'form'
            response['HX-Reswap'] = 'outerHTML'
            response['HX-Trigger-After-Settle'] = 'fail'

            return response
    else:
        form = MeetingForm()

    return render(request, "partials/meet_form.html", {"form": form})


def meet_edit(request, pk):
    meeting = get_object_or_404(Meeting, pk=pk)

    if request.method == "POST":
        form = MeetingForm(request.POST, instance=meeting)
        if form.is_valid():
            meeting = form.save()
            
            response = render(request, "partials/meet_row_table.html", {"meeting": meeting})
            response["HX-Trigger"] = json.dumps({
                "state": "success",
                "message": "La reunión se editó correctamente"
            })
            return response
        else:
            response = render(request, "partials/meet_form.html", {"form": form})
            response['HX-Retarget'] = 'form'
            response['HX-Reswap'] = 'outerHTML'
            response['HX-Trigger-After-Settle'] = 'fail'

            return response
    else:
        form = MeetingForm(instance=meeting)

    return render(
        request,
        "partials/meet_form.html",
        {"form": form, "meeting": meeting}
    )