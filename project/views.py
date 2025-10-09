from django.shortcuts import render, redirect
from .models import Project, Community, Directive, Partner, WaterConnection
from .forms import ProjectForm, CommunityForm, DirectiveForm, PartnerForm, UsersForm, ConnectionForm
from django.db.models import Q
from django.core.paginator import Paginator
from django.urls import reverse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.cache import never_cache
from django.http import HttpResponse
from django.utils import timezone
import json


def project_info_view(request):
    project = Project.objects.first()
    form = ProjectForm(instance=project)
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES, instance=project)
        success = False
        if form.is_valid():
            form.save()
            project = form.instance
            form = ProjectForm(instance=project)
            success = True
        # Si la petición es AJAX (fetch)
        # Retorna solo el template parcial con el indicador de éxito.
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return render(request, 'partials/project_form_partial.html', {'project': project, 'form': form, 'success': success})
        return redirect('project_info')
    # NO es POST (por ejemplo, al cancelar o recargar el bloque), retorna el template parcial sin indicador de éxito.
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'partials/project_form_partial.html', {'project': project, 'form': form})
    return render(request, 'project.html', {'project': project, 'form': form})


# Opciones de paginación
per_page_options = [5, 10, 20, 50]

def community_list(request):
    project = Project.objects.first()
    query = request.GET.get('q', '') 
    page_number = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', per_page_options[1]))

    community_list = Community.objects.all().order_by('name')
    paginator = Paginator(community_list, per_page)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'communities.html',
        {
            'community_search_url': reverse('community_search'),
            'page_obj': page_obj,
            'query': query,
            'per_page': per_page,
            'per_page_options': per_page_options,
            'form': CommunityForm(),
            'project': project,
        }
    )

def community_search(request):
    query = request.GET.get('q', '') 
    page_number = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', per_page_options[1]))

    community_list = Community.objects.filter(
        Q(name__icontains=query) | Q(description__icontains=query)
    ).order_by('name')

    paginator = Paginator(community_list, per_page)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'partials/community_table.html',
        {
            'community_search_url': reverse('community_search'),
            'page_obj': page_obj,
            'query': query,
            'per_page': per_page,
            'per_page_options': per_page_options,
        }
    )

def community_create(request):
    if request.method == "POST":
        form = CommunityForm(request.POST)
        if form.is_valid():
            community = form.save()
            response = render(
                request,
                "partials/community_row_table.html",
                {"community": community}
            )
            response["HX-Trigger"] = json.dumps({
                "state": "success",
                "message": "La comunidad se guardó correctamente"
            })
            return response
        else:
            response = render(request, "partials/community_form.html", {"form": form})
            response['HX-Retarget'] = 'form'
            response['HX-Reswap'] = 'outerHTML'
            response['HX-Trigger-After-Settle'] = 'fail'
            return response
    else:
        form = CommunityForm()

    return render(request, "partials/community_form.html", {"form": form})

def community_edit(request, pk):
    community = get_object_or_404(Community, pk=pk)

    if request.method == "POST":
        form = CommunityForm(request.POST, instance=community)
        if form.is_valid():
            community = form.save()
            response = render(
                request,
                "partials/community_row_table.html",
                {"community": community}
            )
            response["HX-Trigger"] = json.dumps({
                "state": "success",
                "message": "La comunidad se editó correctamente"
            })
            return response
        else:
            response = render(request, "partials/community_form.html", {"form": form})
            response['HX-Retarget'] = 'form'
            response['HX-Reswap'] = 'outerHTML'
            response['HX-Trigger-After-Settle'] = 'fail'
            return response
    else:
        form = CommunityForm(instance=community)

    return render(
        request,
        "partials/community_form.html",
        {"form": form, "community": community}
    )


def directive_list(request):
    project = Project.objects.first()
    query = request.GET.get('q', '') 
    page_number = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', per_page_options[1]))

    directive_list = Directive.objects.all().order_by('-isActive')
    paginator = Paginator(directive_list, per_page)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'directive/directives.html',
        {
            'directive_search_url': reverse('directive_search'),
            'page_obj': page_obj,
            'query': query,
            'per_page': per_page,
            'per_page_options': per_page_options,
            'project': project,
        }
    )

def directive_search(request):
    query = request.GET.get('q', '') 
    page_number = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', per_page_options[1]))

    directive_list = Directive.objects.filter(
        Q(partner__first_name__icontains=query) |
        Q(partner__last_name__icontains=query) |
        Q(partner__dui__icontains=query)
    ).order_by('-isActive')

    paginator = Paginator(directive_list, per_page)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'partials/directive/directive_table.html',
        {
            'directive_search_url': reverse('directive_search'),
            'page_obj': page_obj,
            'query': query,
            'per_page': per_page,
            'per_page_options': per_page_options,
        }
    )

def directive_create(request):
    if request.method == "POST":
        form = DirectiveForm(request.POST)
        if form.is_valid():
            directive = form.save()
            response = render(
                request,
                "partials/directive/directive_create_success.html",
                {"executive": directive},
            )
            response["HX-Trigger"] = json.dumps({"directive:added": {"id": directive.id}})
            return response

        return render(request, "partials/directive/directive_form.html", {"form": form})

    # GET
    form = DirectiveForm()
    return render(request, "partials/directive/directive_form.html", {"form": form})

@never_cache
def partner_search(request):
    q = (request.GET.get('partner_search') or '').strip()

    # Si está vacío, no toques el DOM (HTMX no hace swap)
    if not q:
        return HttpResponse(status=204)

    qs = Partner.objects.all()
    fields = {f.name for f in Partner._meta.get_fields()}
    if 'is_active' in fields:
        qs = qs.filter(is_active=True)
    elif 'isActive' in fields:
        qs = qs.filter(isActive=True)

    # Usa icontains (coincidencias en cualquier parte), más tolerante
    filtro = Q()
    if 'first_name' in fields:
        filtro |= Q(first_name__icontains=q)
    if 'last_name' in fields:
        filtro |= Q(last_name__icontains=q)
    if 'name' in fields:
        filtro |= Q(name__icontains=q)
    if 'dui' in fields:
        filtro |= Q(dui__icontains=q)

    partners = qs.filter(filtro).order_by('first_name', 'last_name', 'id')[:10]

    ctx = {'partners': partners, 'typed': True}
    resp = render(request, 'partials/directive/partner_search_results.html', ctx)
    # blindaje anti-caché
    resp['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resp['Pragma'] = 'no-cache'
    return resp

@require_POST
def directive_deactivate(request, pk):
        executive = get_object_or_404(Directive, pk=pk)
        if not executive.isActive:
            # nada que hacer; no cambies el DOM
            return HttpResponse(status=204)

        executive.isActive = False
        executive.end_date = timezone.localdate()
        executive.save(update_fields=['isActive', 'end_date'])

        # Renderiza SOLO la fila para reemplazarla
        return render(
            request,
            "partials/directive/directive_row_table.html",
            {"executive": executive}
        )

def users_list(request):
    project = Project.objects.first()
    query = request.GET.get('q', '') 
    page_number = request.GET.get('page', 1)

    per_page_options = [5, 10, 20, 50]
    per_page = int(request.GET.get('per_page', per_page_options[1]))

    users_list = Partner.objects.filter(is_superuser=False).order_by('-is_staff')
    paginator = Paginator(users_list, per_page)
    page_obj = paginator.get_page(page_number)

    context = {
        'users_search_url': reverse('users_search'),
        'page_obj': page_obj,
        'query': query,
        'per_page': per_page,
        'per_page_options': per_page_options,
        'project': project,
    }

    # Si la petición viene de HTMX => renderiza solo el contenido parcial
    if request.headers.get('HX-Request'):
        return render(request, "partials/users/users_content.html", context)

    # Si es petición normal => renderiza toda la página
    return render(request, "users/users.html", context)

def users_search(request):
    query = request.GET.get('q', '') 
    page_number = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', per_page_options[1]))

    users_list = Partner.objects.filter(
        Q(is_superuser=False) & (Q(username__icontains=query) | Q(is_staff__icontains=query))
    ).order_by('-is_staff')

    paginator = Paginator(users_list, per_page)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'partials/users/users_table.html',
        {
            'users_search_url': reverse('users_search'),
            'page_obj': page_obj,
            'query': query,
            'per_page': per_page,
            'per_page_options': per_page_options,
        }
    )

def user_create_view(request):
    project = Project.objects.first()
    return render(
        request,
        "partials/users/user_form.html",
        {"project": project}
    )

@require_POST
def user_deactivate(request, pk):
    partner = get_object_or_404(Partner, pk=pk)

    partner.is_staff = False
    partner.save()

    if request.headers.get("HX-Request"):
        response = users_list(request)
        response["HX-Trigger"] = "userDeactivated"
        return response

    return redirect("users_list")

def user_edit(request, pk):
    user = get_object_or_404(Partner, pk=pk)

    # Si es POST, pasamos request.POST
    if request.method == "POST":
        form = UsersForm(request.POST, instance=user)
    else:
        # Si es GET, asignamos initial para el grupo actual
        initial_data = {}
        first_group = user.groups.first()
        if first_group:
            initial_data["groups"] = first_group.pk
        form = UsersForm(instance=user, initial=initial_data)

    if request.method == "POST":
        if form.is_valid():
            form.save()

            if request.headers.get("HX-Request"):
                response = users_list(request)
                response["HX-Trigger"] = "userEdited"
                return response

            return redirect("users_list")
        else:
            response = render(
                request,
                "partials/users/user_form.html",
                {"form": form, "mode": "edit", "user": user},
            )
            response["HX-Target"] = "#main-container"
            response["HX-Swap"] = "innerHTML"
            response["HX-Trigger-After-Settle"] = "fail"
            return response

    return render(
        request,
        "partials/users/user_form.html",
        {"form": form, "mode": "edit", "user": user},
    )


def partners_list(request):
    project = Project.objects.first()
    query = request.GET.get('q', '') 
    page_number = request.GET.get('page', 1)

    per_page_options = [5, 10, 20, 50]
    per_page = int(request.GET.get('per_page', per_page_options[1]))

    partners_list = Partner.objects.filter(is_superuser=False).order_by('-is_active')
    paginator = Paginator(partners_list, per_page)
    page_obj = paginator.get_page(page_number)

    context = {
        'partners_search_url': reverse('partners_search'),
        'page_obj': page_obj,
        'query': query,
        'per_page': per_page,
        'per_page_options': per_page_options,
        'project': project,
    }

    # Si la petición viene de HTMX => renderiza solo el contenido parcial
    if request.headers.get('HX-Request'):
        return render(request, "partials/partner/partners_content.html", context)

    # Si es petición normal => renderiza toda la página
    return render(request, "partner/partners.html", context)

def partners_search(request):
    query = request.GET.get('q', '') 
    page_number = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', per_page_options[1]))

    partners_list = Partner.objects.filter(
        Q(is_superuser=False) &
        (
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(community__name__icontains=query) |
            Q(dui__icontains=query) |
            Q(tel__icontains=query) |
            (
                Q(is_active=True)  if query.lower() == "activo" else
                Q(is_active=False) if query.lower() == "inactivo" else
                Q()  # vacío si no coincide
            )
        )
    ).order_by('-is_active')

    paginator = Paginator(partners_list, per_page)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'partials/partner/partners_table.html',
        {
            'partners_search_url': reverse('partners_search'),
            'page_obj': page_obj,
            'query': query,
            'per_page': per_page,
            'per_page_options': per_page_options,
        }
    )

def partner_create_view(request):
    if request.method == "POST":
        form = PartnerForm(request.POST, request.FILES)
        if form.is_valid():
            partner = form.save()
            if request.headers.get('HX-Request'):
                response = partners_list(request)
                response["HX-Trigger"] = "partnerCreated"
                return response
            return redirect('partners_list')
        else:
            response = render(
                request,
                "partials/partner/partner_form.html",
                {"form": form, "mode": "create"}
            )
            response['HX-Target'] = '#main-container'
            response['HX-Swap'] = 'innerHTML'
            response['HX-Trigger-After-Settle'] = 'fail'
            return response
    else: 
        form = PartnerForm()
    return render(
        request,
        "partials/partner/partner_form.html",
        {"form": form, "mode": "create"}
    )

def partner_view(request, pk):
    partner = get_object_or_404(Partner, pk=pk)
    form = PartnerForm(instance=partner)
    for field in form.fields.values():
        field.disabled = True
    return render(request, "partials/partner/partner_form.html", {"form": form, "mode": "view", "partner": partner})

def partner_edit(request, pk):
    partner = get_object_or_404(Partner, pk=pk)

    if request.method == "POST":
        form = PartnerForm(request.POST, request.FILES, instance=partner)

        if form.is_bound:
            form.data = form.data.copy()
            form.data['dui'] = partner.dui

        if form.is_valid():
            form.save()
            if request.headers.get("HX-Request"):
                response = partners_list(request)
                response["HX-Trigger"] = "partnerEdited"
                return response
            return redirect("partners_list")
        else:
            response = render(
                request,
                "partials/partner/partner_form.html",
                {"form": form, "mode": "edit", "partner": partner},
            )
            response['HX-Target'] = '#main-container'
            response['HX-Swap'] = 'innerHTML'
            response['HX-Trigger-After-Settle'] = 'fail'
            return response
    else:
        form = PartnerForm(instance=partner)

    return render(
        request,
        "partials/partner/partner_form.html",
        {"form": form, "mode": "edit", "partner": partner},
    )

@require_POST
def partner_toggle_active(request, pk):
    partner = get_object_or_404(Partner, pk=pk)

    partner.is_active = not partner.is_active

    # Si se desactiva, quitar is_staff
    if not partner.is_active:
        partner.is_staff = False

    partner.save()

    if request.headers.get("HX-Request"):
        response = partners_list(request)
        response["HX-Trigger"] = (
            "partnerActivated" if partner.is_active else "partnerDeactivated"
        )
        return response

    return redirect("partners_list")


def connections_list(request):
    project = Project.objects.first()
    query = request.GET.get('q', '') 
    page_number = request.GET.get('page', 1)

    per_page_options = [5, 10, 20, 50]
    per_page = int(request.GET.get('per_page', per_page_options[1]))

    connections_list = WaterConnection.objects.all()
    paginator = Paginator(connections_list, per_page)
    page_obj = paginator.get_page(page_number)

    context = {
        'connections_search_url': reverse('connections_search'),
        'page_obj': page_obj,
        'query': query,
        'per_page': per_page,
        'per_page_options': per_page_options,
        'project': project,
    }

    # Si la petición viene de HTMX => renderiza solo el contenido parcial
    if request.headers.get('HX-Request'):
        return render(request, "partials/water_connection/connection_content.html", context)

    # Si es petición normal => renderiza toda la página
    return render(request, "water_connection/water_connection.html", context)

def connections_search(request):
    query = request.GET.get('q', '') 
    page_number = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', per_page_options[1]))

    print("DEBUG connections_search: query param q =", repr(query))
    print("DEBUG connections_search: request.GET =", dict(request.GET))

    connections_list = WaterConnection.objects.filter(
        (Q(description__icontains=query) | Q(responsible__first_name__icontains=query) | Q(responsible__last_name__icontains=query))
    )

    paginator = Paginator(connections_list, per_page)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'partials/water_connection/connection_table.html',
        {
            'connections_search_url': reverse('connections_search'),
            'page_obj': page_obj,
            'query': query,
            'per_page': per_page,
            'per_page_options': per_page_options,
        }
    )

@require_POST
def connection_toggle_active(request, pk):
    connection = get_object_or_404(WaterConnection, pk=pk)

    connection.is_active = not connection.is_active

    connection.save()

    if request.headers.get("HX-Request"):
        response = connections_list(request)
        response["HX-Trigger"] = (
            "connectionActivated" if connection.is_active else "connectionDeactivated"
        )
        return response

    return redirect("connections_list")

def partner_search_view(request):
    q = (request.GET.get("qq") or "").strip()
    target = request.GET.get("target")  # ejemplo: 'owner' o 'responsible'

    # Si no hay query, no tocar el DOM
    if not q:
        return HttpResponse(status=204)

    partners = (
        Partner.objects.filter(
            Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(dui__icontains=q)
        )
        .filter(is_active=True)
        .order_by("first_name", "last_name")[:10]
    )

    ctx = {
        "partners": partners,
        "target": target,  # para saber a qué campo asignar
    }
    # Corrige la ruta del template:
    response = render(request, "partials/partner/partner_search_results.html", ctx)
    response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response["Pragma"] = "no-cache"
    return response

def connection_create_view(request):
    project = Project.objects.first()
    if request.method == "POST":
        data = request.POST.copy()
        data["acquisition_price"] = project.connection_price
        # Si responsible viene vacío, asigna el owner
        if not data.get("responsible") and data.get("owner"):
            data["responsible"] = data["owner"]
        form = ConnectionForm(data)
        if form.is_valid():
            form.save() 
            if request.headers.get('HX-Request'):
                response = HttpResponse()
                response['HX-Redirect'] = reverse('connections_list')
                return response
        else:
            # Si es HTMX → devolver solo el fragmento del form
            if request.headers.get("HX-Request"):
                response = render(
                    request,
                    "partials/water_connection/connection_form.html",
                    {"form": form}
                )
                response["HX-Retarget"] = "#connection-form"
                response["HX-Reswap"] = "outerHTML"
                response["HX-Trigger-After-Settle"] = "fail"
                return response
            # Si no es HTMX → devolver toda la página (para debug o carga normal)
            return render(
                request,
                "water_connection/connection_page.html",
                {"form": form}
            )
    else:
        form = ConnectionForm()
        form = ConnectionForm(initial={"acquisition_price": project.connection_price})

    return render(request, "partials/water_connection/connection_form.html", {"form": form})

def connection_edit_view(request, pk):
    connection = get_object_or_404(WaterConnection, pk=pk)
    if request.method == "POST":
        data = request.POST.copy()
        # Setea los campos deshabilitados manualmente
        data["owner"] = connection.owner.id
        data["date"] = connection.date.strftime("%Y-%m-%d")
        data["acquisition_price"] = str(connection.acquisition_price)
        form = ConnectionForm(data, instance=connection)
        if form.is_valid():
            form.save()
            if request.headers.get("HX-Request"):
                response = HttpResponse()
                response['HX-Redirect'] = reverse('connections_list')
                return response
            return redirect('connections_list')
        else:
            # Si es HTMX → devolver solo el fragmento del form de edición
            if request.headers.get("HX-Request"):
                return render(
                    request,
                    "partials/water_connection/connection_edit_form.html",
                    {"form": form, "connection": connection}
                )
            # Si no es HTMX → devolver toda la página (para debug o carga normal)
            return render(
                request,
                "water_connection/connection_page.html",
                {"form": form, "connection": connection}
            )
    else:
        form = ConnectionForm(instance=connection)
    return render(
        request,
        "partials/water_connection/connection_edit_form.html",
        {"form": form, "connection": connection}
    )