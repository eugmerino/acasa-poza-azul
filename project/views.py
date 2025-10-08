from django.shortcuts import render, redirect
from .models import Project, Community, Directive, Partner
from .forms import ProjectForm, CommunityForm, DirectiveForm 
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