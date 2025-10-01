from django.urls import path
from . import views

urlpatterns = [
    path('', views.meet_list, name='meet_list'),
    path("buscar/", views.meet_search, name="meet_search"),
    path("crear/", views.meet_create, name="meet_create"),
    path("editar/<int:pk>/", views.meet_edit, name="meet_edit"),
    path("lista_Asistencias", views.attendance_list, name="attendance_list"),
    path("buscar_Asistencia/", views.attendance_search, name="attendance_search"),
    path("crear_Asistencia/", views.attendance_create, name="attendance_create"),
    path("Asistencia/", views.attendance, name="attendance"),
]