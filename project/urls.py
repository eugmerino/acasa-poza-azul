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
    path('seguridad/usuarios/editar/<int:pk>/', views.user_edit, name='user_edit'),
    path("seguridad/usuarios/nuevo/", views.user_create_view, name="user_create"),
    path("seguridad/usuarios/estado/<int:pk>", views.user_deactivate, name="user_deactivate"),
    path('proyecto/socios/', views.partners_list, name='partners_list'),
    path('proyecto/socios/buscar/', views.partners_search, name='partners_search'),
    path("proyecto/socios/nuevo/", views.partner_create_view, name="partner_create"),
    path("proyecto/socios/ver/<int:pk>/", views.partner_view, name="partner_view"),
    path("proyecto/socios/editar/<int:pk>/", views.partner_edit, name="partner_edit"),
    path("proyecto/socios/estado/<int:pk>", views.partner_toggle_active, name="partner_toggle_active"),
    path('proyecto/acometidas/', views.connections_list, name='connections_list'),
    path('proyecto/acometidas/buscar/', views.connections_search, name='connections_search'),
    path("proyecto/acometidas/nuevo/", views.partner_create_view, name="partner_create"),
    path("proyecto/acometidas/ver/<int:pk>/", views.partner_view, name="partner_view"),
    path("proyecto/acometidas/editar/<int:pk>/", views.partner_edit, name="partner_edit"),
    path("proyecto/acometidas/estado/<int:pk>", views.connection_toggle_active, name="connection_toggle_active"),

]
