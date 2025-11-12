from django.shortcuts import render, get_object_or_404
from .models import Meeting, Attendance
from project.models import Project
from django.http import HttpResponse
from django.template.loader import render_to_string
import weasyprint
from datetime import date
import json
from django.db.models import Q
from django.core.paginator import Paginator
from django.urls import reverse
from meeting.forms import MeetingForm
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.utils.timezone import localtime, now
from project.models import Partner




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
        'meeting/reuniones.html',
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
            'today': timezone.localdate(),
            'current_time': timezone.localtime().time(),
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
# LISTA DE ASISTENCIAS
# ---------------------------------------------------------
def attendance_list(request):
    project = Project.objects.first()
    query = request.GET.get('q', '')
    page_number = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', per_page_options[1]))

    # 🔹 Obtener todas las asistencias, incluyendo datos relacionados
    attendance_list = Attendance.objects.select_related('meeting', 'partner').filter(
        Q(partner__is_active=True) & (
            Q(meeting__title__icontains=query) |
            Q(partner__first_name__icontains=query) |
            Q(partner__last_name__icontains=query)
        )
    ).order_by('-meeting__date', '-meeting__start_time')

    paginator = Paginator(attendance_list, per_page)
    page_obj = paginator.get_page(page_number)

    now_local = localtime()

    return render(
        request,
        'meeting/attendance.html',
        {
            'attendance_search_url': reverse('attendance_search'),
            'page_obj': page_obj,
            'query': query,
            'per_page': per_page,
            'per_page_options': per_page_options,
            'form': AttendanceForm(),
            'project': project,
            'today': now_local.date(),
            'current_time': now_local.time(),
        }
    )

# ---------------------------------------------------------
# BÚSQUEDA DE ASISTENCIAS
# ---------------------------------------------------------
def attendance_search(request):
    project = Project.objects.first()
    today = localtime().date()
    now_time = localtime().time().replace(microsecond=0)

    active_meeting = Meeting.objects.filter(
        date=today,
        start_time__lte=now_time,
        end_time__gte=now_time,
        isActive=True
    ).first()

    partners = Partner.objects.filter(community__project=project, is_superuser=False, is_active=True)
    query = request.GET.get('q', '').strip()

    if query:
        partners = partners.filter(
            Q(is_active=True) & (
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(dui__icontains=query) |
                Q(community__name__icontains=query)
            )
        )

    attended_partner_ids = set()
    if active_meeting:
        attended_partner_ids = set(active_meeting.attendances.values_list('partner_id', flat=True))

    return render(request, "partials/meeting/attendance_content.html", {
        "project": project,
        "active_meeting": active_meeting,
        "partners": partners,
        "attended_partner_ids": attended_partner_ids,
        "attendance_search_url": reverse('attendance_search'),
        "query": query,
    })



def attendance(request):
    project = Project.objects.first()
    today = localtime().date()
    now_time = localtime().time().replace(microsecond=0)

    # Buscar reunión activa en este momento
    active_meeting = Meeting.objects.filter(
        date=today,
        start_time__lte=now_time,
        end_time__gte=now_time,
        isActive=True
    ).first()

    # Filtrar solo socios del proyecto que no sean superusuarios
    partners = Partner.objects.filter(
        community__project=project,
        is_superuser=False,
        is_active=True
    )

    if request.method == "POST" and active_meeting:
        for partner in partners:
            checkbox_name = f"attendance_{partner.id}"
            attended = checkbox_name in request.POST

            if attended:
                Attendance.objects.get_or_create(meeting=active_meeting, partner=partner)
            else:
                Attendance.objects.filter(meeting=active_meeting, partner=partner).delete()

        # 🔹 Recalcular IDs después de guardar
        attended_partner_ids = set(
            active_meeting.attendances.values_list('partner_id', flat=True)
        )

        # 🔹 Respuesta HTMX con header para SweetAlert2
        if request.headers.get("Hx-Request") == "true":
            response = render(request, "partials/meeting/attendance_content.html", {
                "project": project,
                "active_meeting": active_meeting,
                "partners": partners,
                "attended_partner_ids": attended_partner_ids,
            })
            response["HX-Trigger"] = json.dumps({
                "state": "success",
                "message": f"Asistencias actualizadas para la reunión: {active_meeting.title}"
            })
            return response

        return redirect("attendance")

    # GET o no hay POST
    attended_partner_ids = set()
    if active_meeting:
        attended_partner_ids = set(
            active_meeting.attendances.values_list('partner_id', flat=True)
        )

    # Template parcial si HTMX, sino la página completa
    template = (
        "partials/meeting/attendance_content.html"
        if request.headers.get("Hx-Request") == "true"
        else "meeting/attendance.html"
    )

    return render(request, template, {
        "project": project,
        "active_meeting": active_meeting,
        "partners": partners,
        "attended_partner_ids": attended_partner_ids,
    })
    project = Project.objects.first()
    today = localtime().date()
    now_time = localtime().time().replace(microsecond=0)

    # Buscar reunión activa en este momento
    active_meeting = Meeting.objects.filter(
        date=today,
        start_time__lte=now_time,
        end_time__gte=now_time,
        isActive=True
    ).first()

     # Crear set de IDs de socios que ya tienen asistencia
    attended_partner_ids = set()
    if active_meeting:
        attended_partner_ids = set(
            active_meeting.attendances.values_list('partner_id', flat=True)
        )

    # Filtrar solo socios del proyecto y que no sean superusuarios
    partners = Partner.objects.filter(
        community__project=project,
        is_superuser=False
    )

    if request.method == "POST" and active_meeting:
        for partner in partners:
            checkbox_name = f"attendance_{partner.id}"
            attended = checkbox_name in request.POST

            if attended:
                # Solo guardar asistencia si fue marcado
                Attendance.objects.get_or_create(
                    meeting=active_meeting,
                    partner=partner
                )
            else:
                # Si estaba guardado y se desmarca, eliminarlo
                Attendance.objects.filter(
                    meeting=active_meeting,
                    partner=partner
                ).delete()

        # 🔹 Devolver solo el fragmento si es HTMX
        if request.headers.get("Hx-Request") == "true":
            return render(request, "partials/meeting/attendance_content.html", {
                "project": project,
                "active_meeting": active_meeting,
                "attended_partner_ids": attended_partner_ids,
                "partners": partners,
            })

        return redirect("attendance")

    # 🔹 Si es HTMX también devolver solo el fragmento
    template = (
        "partials/meeting/attendance_content.html"
        if request.headers.get("Hx-Request") == "true"
        else "meeting/attendance.html"
    )

    return render(request, template, {
        "project": project,
        "active_meeting": active_meeting,
        "attended_partner_ids": attended_partner_ids,
        "partners": partners,
    })

def attendance_pdf(request, meeting_id):
    meeting = get_object_or_404(Meeting, id=meeting_id)

    # proyecto asociado o por defecto
    default_project = Project.objects.first()
    project_for_pdf = getattr(meeting, 'project', default_project) or default_project

    # Obtener todos los socios del proyecto excluyendo superusers y solo activos
    project_partners = Partner.objects.filter(
        community__project=project_for_pdf,
        is_superuser=False,
        is_active=True
    )

    # Asistentes y no asistentes (solo entre los partners del proyecto, sin superusers)
    asistentes = project_partners.filter(attendances__meeting=meeting).distinct()
    no_asistentes = project_partners.exclude(attendances__meeting=meeting).distinct()

    # Totales
    total_asistencias = asistentes.count()
    total_socios = project_partners.count()
    total_inasistentes = total_socios - total_asistencias

    # Logo seguro
    logo_url = None
    if project_for_pdf and getattr(project_for_pdf, 'logo', None):
        try:
            logo_url = request.build_absolute_uri(project_for_pdf.logo.url)
        except Exception:
            logo_url = None

    html = render_to_string("partials/meeting/attendance_pdf.html", {
        'project': project_for_pdf,
        'logo_url': logo_url,
        'meeting': meeting,
        'asistentes': asistentes,
        'no_asistentes': no_asistentes,
        'today': date.today(),
        'total_asistencias': total_asistencias,
        'total_socios': total_socios,
        'total_inasistentes': total_inasistentes,
    })

    response = HttpResponse(content_type="application/pdf")
    response['Content-Disposition'] = f'inline; filename="asistencia_{meeting.id}.pdf"'
    weasyprint.HTML(string=html).write_pdf(response)
    return response

def information(request):
    project = Project.objects.first()
    page_number = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', per_page_options[1]))

    now = timezone.localtime()

    # ✅ Solo reuniones ya realizadas (fecha pasada o finalizadas hoy)
    from django.db.models import Q
    meet_list = Meeting.objects.filter(
        Q(date__lt=now.date()) |
        Q(date=now.date(), end_time__lt=now.time())
    ).order_by('-date', '-start_time')

    paginator = Paginator(meet_list, per_page)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'meeting/information.html',  # 👈 nuevo template
        {
            'page_obj': page_obj,
            'project': project,
            'per_page': per_page,
            'per_page_options': per_page_options,
        }
    )

def information_search(request):
    query = request.GET.get('q', '') 
    page_number = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', per_page_options[1]))

    today = timezone.localdate()
    now = timezone.localtime().time()

    meet_list = Meeting.objects.filter(
        Q(date__lt=today) | (Q(date=today) & Q(end_time__lt=now))
    ).filter(
        Q(title__icontains=query) | Q(date__icontains=query)
    ).order_by('-date', '-end_time')

    paginator = Paginator(meet_list, per_page)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'partials/meet/information_table.html',
        {
            'information_search_url': reverse('information_search'),
            'page_obj': page_obj,
            'query': query,
            'per_page': per_page,
            'per_page_options': per_page_options,
            'today': timezone.localdate(),
            'current_time': timezone.localtime().time(),
        }
    )