from django.urls import path
from . import views
from .views import meet_pdf


urlpatterns = [
    path('', views.meet_list, name='meet_list'),
    path("buscar/", views.meet_search, name="meet_search"),
    path("crear/", views.meet_create, name="meet_create"),
    path('reuniones/pdf/', meet_pdf, name='meet_pdf'),
    path("editar/<int:pk>/", views.meet_edit, name="meet_edit"),
    path("lista_Asistencias", views.attendance_list, name="attendance_list"),
    path("buscar_Asistencia/", views.attendance_search, name="attendance_search"),
    path("Asistencia/", views.attendance, name="attendance"),
    
]