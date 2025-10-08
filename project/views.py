from django.shortcuts import render, redirect
from .models import Project, Community, Partner, WaterConnection
from .forms import ProjectForm, CommunityForm, PartnerForm, UsersForm
from django.db.models import Q
from django.core.paginator import Paginator
from django.urls import reverse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST
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