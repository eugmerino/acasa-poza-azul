from django.shortcuts import render, redirect
from .models import Project, Community
from .forms import ProjectForm
from django.db.models import Q
from django.core.paginator import Paginator
from django.urls import reverse


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

def community_list(request):
    per_page_options = [5, 10, 20, 50]

    query = request.GET.get('q', '') 
    page_number = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', per_page_options[1]))

    community_list = Community.objects.all().order_by('-name')
    paginator = Paginator(community_list, per_page)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'community.html',
        {
            'community_search_url': reverse('community_search'),
            'page_obj': page_obj,
            'query': query,
            'per_page': per_page,
            'per_page_options': per_page_options,
        }
    )

def community_search(request):
    per_page_options = [5, 10, 20, 50]

    query = request.GET.get('q', '') 
    page_number = request.GET.get('page', 1)
    per_page = int(request.GET.get('per_page', per_page_options[1]))

    community_list = Community.objects.filter(
        Q(name__icontains=query)
    ).order_by('-name')

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