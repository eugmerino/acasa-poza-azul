from django.urls import path
from . import views

urlpatterns = [
    path('project/', views.project_info_view, name='project_info'),
    path('comunidades/', views.community_list, name='community_list'),
    path('comunidades/buscar/', views.community_search, name='community_search'),
    path('comunidades/crear/', views.community_create, name='community_create'),
    path('comunidades/editar/<int:pk>/', views.community_edit, name='community_edit'),
    path('seguridad/usuarios/', views.users_list, name='users_list'),
    path('seguridad/usuarios/buscar/', views.users_search, name='users_search'),
    path("seguridad/usuarios/nuevo/", views.user_create_view, name="user_create"),
    path('proyecto/socios/', views.partners_list, name='partners_list'),
    path('proyecto/socios/buscar/', views.partners_search, name='partners_search'),
    path("proyecto/socios/nuevo/", views.partner_create_view, name="partner_create"),
]
