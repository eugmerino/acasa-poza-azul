from django.shortcuts import render
from project.models import Project

def inicio(request):
    project = Project.objects.first()
    return render(request, "home.html", {"project": project})
