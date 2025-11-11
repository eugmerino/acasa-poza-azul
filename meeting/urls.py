from django.urls import path
from . import views


urlpatterns = [
    path('', views.meet_list, name='meet_list'),
    path("buscar/", views.meet_search, name="meet_search"),
    path("crear/", views.meet_create, name="meet_create"),
    path("editar/<int:pk>/", views.meet_edit, name="meet_edit"),
    path("lista_Asistencias", views.attendance_list, name="attendance_list"),
    path("buscar_Asistencia/", views.attendance_search, name="attendance_search"),
    path("Asistencia/", views.attendance, name="attendance"),
    path('asistencias/pdf/<int:meeting_id>/', views.attendance_pdf, name='attendance_pdf'),
    path("Informes/", views.information, name="information"),
    path("Informes_Buscar/", views.information_search, name="information_search"),
]