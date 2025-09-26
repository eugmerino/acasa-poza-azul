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
from meeting.models import Attendance
from meeting.forms import AttendanceForm
from django.utils.timezone import now
from django.utils import timezone


per_page_options = [5, 10, 20, 50]

def meet_list(request):
    project = Project.objects.first()
    query = request.GET.get('q', '') 
    page_number = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', per_page_options[1]))

    meet_list = Meeting.objects.all().order_by('-isActive')
    paginator = Paginator(meet_list, per_page)
    page_obj = paginator.get_page(page_number)

    now = timezone.localtime()

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
            'today': now.date(),
            'current_time': now.time(), 
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
        'partials/meet/meet_table.html',
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
            response = render(request, "partials/meet/meet_row_table.html", {"meeting": meeting})
            response["HX-Trigger"] = json.dumps({
                "state": "success",
                "message": "La reunión se guardó correctamente"
            })

            return response
        else:
            response = render(request, "partials/meet/meet_form.html", {"form": form})
            response['HX-Retarget'] = 'form'
            response['HX-Reswap'] = 'outerHTML'
            response['HX-Trigger-After-Settle'] = 'fail'

            return response
    else:
        form = MeetingForm()

    return render(request, "partials/meet/meet_form.html", {"form": form})


def meet_edit(request, pk):
    meeting = get_object_or_404(Meeting, pk=pk)

    if request.method == "POST":
        form = MeetingForm(request.POST, instance=meeting)
        if form.is_valid():
            meeting = form.save()
            
            response = render(request, "partials/meet/meet_row_table.html", {"meeting": meeting})
            response["HX-Trigger"] = json.dumps({
                "state": "success",
                "message": "La reunión se editó correctamente"
            })
            return response
        else:
            response = render(request, "partials/meet/meet_form.html", {"form": form})
            response['HX-Retarget'] = 'form'
            response['HX-Reswap'] = 'outerHTML'
            response['HX-Trigger-After-Settle'] = 'fail'

            return response
    else:
        form = MeetingForm(instance=meeting)

    return render(
        request,
        "partials/meet/meet_form.html",
        {"form": form, "meeting": meeting}
    )


 
# ---------------------------------------------------------
# LISTA DE ASISTENCIAS (solo reunión en proceso)
# ---------------------------------------------------------
def attendance_list(request):
    project = Project.objects.first()
    current_time = now().time()
    today = now().date()

    # Buscar reunión activa en este momento
    active_meeting = Meeting.objects.filter(
        date=today,
        start_time__lte=current_time,
        end_time__gte=current_time,
        isActive=True
    ).first()

    if active_meeting:
        attendance_list = Attendance.objects.filter(meeting=active_meeting).order_by('-id')
    else:
        attendance_list = Attendance.objects.none()

    paginator = Paginator(attendance_list, 10)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(
        request,
        'attendance.html',
        {
            'attendance_search_url': reverse('attendance_search'),
            'page_obj': page_obj,
            'project': project,
            'form': AttendanceForm(),
            'active_meeting': active_meeting,
        }
    )

# ---------------------------------------------------------
# BÚSQUEDA DE ASISTENCIAS (solo reunión en proceso)
# ---------------------------------------------------------
def attendance_search(request):
    query = request.GET.get('q', '')
    current_time = now().time()
    today = now().date()

    active_meeting = Meeting.objects.filter(
        date=today,
        start_time__lte=current_time,
        end_time__gte=current_time,
        isActive=True
    ).first()

    if active_meeting:
        attendance_list = Attendance.objects.filter(
            meeting=active_meeting
        ).filter(
            Q(partner__name__icontains=query)
        ).order_by('-id')
    else:
        attendance_list = Attendance.objects.none()

    paginator = Paginator(attendance_list, 10)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(
        request,
        'partials/attendance/attendance_table.html',
        {
            'attendance_search_url': reverse('attendance_search'),
            'page_obj': page_obj,
            'query': query,
        }
    )

# ---------------------------------------------------------
# CREAR ASISTENCIA (solo reunión en proceso)
# ---------------------------------------------------------
def attendance_create(request):
    current_time = now().time()
    today = now().date()

    # Buscar reunión activa en este momento
    active_meeting = Meeting.objects.filter(
        date=today,
        start_time__lte=current_time,
        end_time__gte=current_time,
        isActive=True
    ).first()

    if not active_meeting:
        # No hay reunión en proceso, no se muestra el form
        return render(request, "partials/attendance/attendance_empty.html")

    if request.method == "POST":
        form = AttendanceForm(request.POST)
        if form.is_valid():
            attendance = form.save(commit=False)
            attendance.meeting = active_meeting
            attendance.save()

            response = render(
                request,
                "partials/attendance/attendance_row_table.html",
                {"attendance": attendance}
            )
            response["HX-Trigger"] = json.dumps({
                "state": "success",
                "message": f"Asistencia registrada en la reunión: {active_meeting.title}"
            })
            return response
        else:
            response = render(request, "partials/attendance/attendance_form.html", {"form": form})
            response['HX-Retarget'] = 'form'
            response['HX-Reswap'] = 'outerHTML'
            response['HX-Trigger-After-Settle'] = 'fail'
            return response
    else:
        form = AttendanceForm()

    return render(
        request,
        "partials/attendance/attendance_form.html",
        {"form": form, "meeting": active_meeting}
    )




def attendance(request):
    project = Project.objects.first()
    today = now().date()
    current_time = now().time().replace(microsecond=0)
    print(Meeting.objects.filter(
            date=today, 
            start_time__lte=current_time,
            end_time__gte=current_time,
            isActive=True
        ).first()
    )


    # Buscar reunión activa en este momento
    active_meeting = Meeting.objects.filter(
        date=today,
        start_time__lte=current_time,
        end_time__gte=current_time,
        isActive=True
    ).first()

    return render(
        request,
        'meeting/attendance.html',
        {
            'project': project,
            'active_meeting': active_meeting,
        }
    )
