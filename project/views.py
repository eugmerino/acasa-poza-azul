from django.shortcuts import render, redirect
from .models import Project
from .forms import ProjectForm

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