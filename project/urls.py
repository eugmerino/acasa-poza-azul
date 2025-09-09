from django.urls import path
from . import views

urlpatterns = [
    path('project/', views.project_info_view, name='project_info'),
]    